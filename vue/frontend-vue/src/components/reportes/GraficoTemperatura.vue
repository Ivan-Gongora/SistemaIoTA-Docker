<template>
  <div class="grafico-combinado-container" :class="{ 'theme-dark': isDark }">
    <div v-if="loading && !hasData" class="loading-overlay">
      <div class="spinner"></div>
      <p>Procesando lectura térmica...</p>
    </div>
    <div v-else-if="error" class="error-message">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
    </div>
    <div v-else-if="!hasData && !loading" class="no-data-message">
      <i class="bi bi-info-circle-fill"></i> Sin registros de temperatura.
    </div>
    <VChart v-show="hasData && !error" :option="chartOption" class="chart" autoresize />
    <div v-if="loading && hasData" class="updating-badge">Actualizando...</div>
  </div>
</template>

<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent, ToolboxComponent, MarkLineComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { ref, watch, computed, onBeforeUnmount } from 'vue';

use([CanvasRenderer, LineChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent, ToolboxComponent, MarkLineComponent]);

const emit = defineEmits(['estadisticas']);

const props = defineProps({
  campos: { type: Array, required: true },
  fechaInicio: { type: String, required: true },
  fechaFin: { type: String, required: true },
  isDark: { type: Boolean, default: false },
  limites: { type: Object, default: () => ({ tempMin: 20, tempMax: 26 }) },
  metodoCarga: { type: String, default: 'optimizado' }
});

const loading = ref(false);
const error = ref(null);
const chartOption = ref({});
const hasData = ref(false);
let abortController = null;

const gridColor = computed(() => props.isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)');
const textColor = computed(() => props.isDark ? '#E4E6EB' : '#333333');
const tooltipBgColor = computed(() => props.isDark ? '#2B2B40' : '#ffffff');
const camposIdsStr = computed(() => props.campos.map(c => c.id).join(','));

const extraerEstadisticasSeguras = (valores) => {
  if (Array.isArray(valores) && valores.length > 0 && valores[0]?.estadisticas_globales) {
    return valores[0].estadisticas_globales;
  }
  let sum = 0, count = 0, min = Infinity, max = -Infinity, textFreq = {};
  if (Array.isArray(valores)) {
    valores.forEach(v => {
        let val = parseFloat(v.valor);
        if (!isNaN(val) && v.valor !== null && v.valor !== '') {
            sum += val; count++;
            if (val < min) min = val;
            if (val > max) max = val;
        } else if (v.valor_texto || v.valor) {
            let txt = String(v.valor_texto || v.valor).trim();
            if (txt) textFreq[txt] = (textFreq[txt] || 0) + 1;
        }
    });
  }
  return {
      min: count > 0 ? min : null, max: count > 0 ? max : null, avg: count > 0 ? sum / count : null,
      es_texto: count === 0 && Object.keys(textFreq).length > 0,
      top_textos: Object.entries(textFreq).sort((a,b)=>b[1]-a[1]).slice(0,3).map(e=>({texto:e[0], conteo:e[1]}))
  };
};

const fetchCampoData = async (campo, signal) => {
  const token = localStorage.getItem('accessToken');
  const url = new URL(`${window.API_BASE_URL}/api/valores/historico-campo/${campo.id}`);
  url.searchParams.append('fecha_inicio', props.fechaInicio);
  url.searchParams.append('fecha_fin', props.fechaFin);
  url.searchParams.append('metodo_carga', props.metodoCarga);

  try {
    const response = await fetch(url.toString(), { headers: { 'Authorization': `Bearer ${token}` }, signal });
    if (!response.ok) throw new Error(`Fallo al cargar ${campo.nombre}.`);
    return await response.json();
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    return [];
  }
};

const cargarDatosCombinados = async () => {
  if (abortController) abortController.abort();
  abortController = new AbortController();
  const signal = abortController.signal;

  loading.value = true;
  error.value = null;

  if (props.campos.length === 0) {
    hasData.value = false;
    loading.value = false;
    return;
  }

  try {
    const allSeries = [];
    let statsEmit = null;
    let hayTexto = false;
    let dataFound = false;

    const dataPromises = props.campos.map(campo => fetchCampoData(campo, signal));
    const results = await Promise.all(dataPromises);

    results.forEach((valores, index) => {
      const campo = props.campos[index];
      if (Array.isArray(valores) && valores.length > 0) {
        const stats = extraerEstadisticasSeguras(valores);
        
        if (stats.es_texto) {
           hayTexto = true;
           return;
        }

        dataFound = true;
        if (!statsEmit) statsEmit = stats;

        const valoresValidos = valores.filter(v => v.valor !== null && v.valor !== '' && !isNaN(parseFloat(v.valor)));

        allSeries.push({
          name: campo.nombre,
          type: 'line',
          sampling: 'lttb',
          large: true,
          data: valoresValidos.map(v => [v.fecha_hora_lectura, parseFloat(v.valor)]),
          smooth: true,
          showSymbol: false,
          itemStyle: { color: '#E74C3C' },
          lineStyle: { width: 3 },
          areaStyle: { color: 'rgba(231, 76, 60, 0.1)' },
          markLine: { 
            data: [
               { yAxis: props.limites.tempMin, name: 'Min', lineStyle: { color: '#E74C3C', type: 'dashed' } },
               { yAxis: props.limites.tempMax, name: 'Max', lineStyle: { color: '#E74C3C', type: 'dashed' } }
            ], 
            symbol: 'none' 
          }
        });
      }
    });

    if (dataFound && statsEmit) {
      emit('estadisticas', {
        id: props.campos[0].id,
        nombre: props.campos[0].nombre,
        unidad: '°C',
        min: statsEmit.min !== null ? parseFloat(statsEmit.min).toFixed(1) : '-',
        max: statsEmit.max !== null ? parseFloat(statsEmit.max).toFixed(1) : '-',
        avg: statsEmit.avg !== null ? parseFloat(statsEmit.avg).toFixed(1) : '-',
        es_texto: false,
        claseColor: 'text-danger'
      });
      updateChartOptions(allSeries);
      hasData.value = true;
    } else {
      hasData.value = false;
      error.value = hayTexto ? 'Los datos contienen texto. Gráfica incompatible.' : 'Registros vacíos en el servidor.';
    }
  } catch (err) {
    if (err.name === 'AbortError') return;
    error.value = err.message;
    hasData.value = false;
  } finally {
    if (!signal.aborted) loading.value = false;
  }
};

const updateChartOptions = (series) => {
  chartOption.value = {
    title: { text: 'Variación de Temperatura', left: 'center', textStyle: { color: textColor.value } },
    tooltip: { trigger: 'axis', backgroundColor: tooltipBgColor.value, textStyle: { color: textColor.value } },
    toolbox: { show: true, feature: { magicType: { type: ['line', 'bar'], title: { line: 'Línea', bar: 'Barras' } }, saveAsImage: { show: true, title: 'Exportar' } }, iconStyle: { borderColor: textColor.value } },
    grid: { left: 50, right: 30, bottom: 65, top: 50 },
    xAxis: { type: 'time', axisLine: { lineStyle: { color: gridColor.value } }, axisLabel: { color: textColor.value } },
    yAxis: { type: 'value', axisLabel: { color: textColor.value, formatter: '{value}°C' }, splitLine: { lineStyle: { color: gridColor.value } }, scale: true },
    dataZoom: [{ type: 'slider', bottom: 5, textStyle: { color: textColor.value }, height: 16 }, { type: 'inside' }],
    series: series
  };
};

watch(() => [camposIdsStr.value, props.fechaInicio, props.fechaFin, props.metodoCarga], cargarDatosCombinados, { immediate: true });
watch(() => props.isDark, () => { if (hasData.value) updateChartOptions(chartOption.value.series); });

onBeforeUnmount(() => {
  if (abortController) abortController.abort();
});
</script>

<style scoped>
.grafico-combinado-container { position: relative; width: 100%; height: 360px; background-color: #FFFFFF; border-radius: 12px; border: 1px solid rgba(0, 0, 0, 0.05); display: flex; align-items: center; justify-content: center; flex-direction: column; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
.grafico-combinado-container.theme-dark { background-color: #2B2B40; border-color: #3C3C55; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
.chart { width: 100%; height: 100%; padding: 12px; }
.loading-overlay, .error-message, .no-data-message { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: rgba(255, 255, 255, 0.8); z-index: 10; font-weight: 700; color: #333; padding: 20px; text-align: center; }
.grafico-combinado-container.theme-dark .loading-overlay, .grafico-combinado-container.theme-dark .error-message, .grafico-combinado-container.theme-dark .no-data-message { background-color: rgba(43, 43, 64, 0.9); color: #E4E6EB; }
.spinner { border: 4px solid rgba(0, 0, 0, 0.1); border-left-color: #E74C3C; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 10px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.error-message i, .no-data-message i { margin-right: 8px; font-size: 1.3em; }
.error-message { color: #E74C3C; }
.no-data-message { color: #3498DB; }
.updating-badge { position: absolute; top: 10px; right: 10px; background: rgba(231, 76, 60, 0.9); color: white; padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; z-index: 5; }
</style>