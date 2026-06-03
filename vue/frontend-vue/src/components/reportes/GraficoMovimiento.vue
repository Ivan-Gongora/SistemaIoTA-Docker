<template>
  <div class="grafico-combinado-container" :class="{ 'theme-dark': isDark }">
    <div v-if="loading && !hasData" class="loading-overlay">
      <div class="spinner"></div>
      <p>Analizando eventos de movimiento...</p>
    </div>
    <div v-else-if="error" class="error-message">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
    </div>
    <div v-else-if="!hasData && !loading" class="no-data-message">
      <i class="bi bi-info-circle-fill"></i> Sin registros de presencia en este periodo.
    </div>
    <VChart v-show="hasData && !error" :option="chartOption" class="chart" autoresize />
    <div v-if="loading && hasData" class="updating-badge">Actualizando...</div>
  </div>
</template>

<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent, ToolboxComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { ref, watch, computed, onBeforeUnmount } from 'vue';

use([CanvasRenderer, LineChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent, ToolboxComponent]);

const emit = defineEmits(['estadisticas']);

const props = defineProps({
  campos: { type: Array, required: true },
  fechaInicio: { type: String, required: true },
  fechaFin: { type: String, required: true },
  isDark: { type: Boolean, default: false },
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
const isPuro = computed(() => props.metodoCarga === 'puro');
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

    const yAxis = {
        type: 'value',
        name: isPuro.value ? 'Estado' : 'Actividad (min/h)',
        axisLine: { show: true, lineStyle: { color: '#8A2BE2' } },
        axisLabel: { color: textColor.value, formatter: function(val) { return isPuro.value ? (val === 1 ? 'Activo' : 'Inactivo') : val; } },
        splitLine: { lineStyle: { color: gridColor.value } },
        min: 0,
        max: isPuro.value ? 1 : 60,
        splitNumber: isPuro.value ? 1 : 4
    };

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
        const valoresValidos = valores.filter(v => v.valor !== null && v.valor !== '' && !isNaN(parseFloat(v.valor)));

        let totalActive = 0;
        valoresValidos.forEach(v => {
            let val = parseFloat(v.valor);
            if (val < 0) val = 0;
            if (isPuro.value) { val = val > 0 ? 1 : 0; }
            totalActive += val;
        });

        let divisor = isPuro.value ? 1 : 60;
        let totalPossible = valoresValidos.length * divisor;
        let occupancy = totalPossible > 0 ? ((totalActive / totalPossible) * 100).toFixed(1) : 0;
        if (occupancy > 100) occupancy = 100.0;

        if (!statsEmit) {
            statsEmit = { avg: occupancy, min: 0, max: isPuro.value ? 1 : 60 };
        }

        allSeries.push({
          name: campo.nombre,
          type: 'line',
          step: 'end',
          sampling: 'lttb',
          large: true,
          showSymbol: false,
          data: valoresValidos.map(v => {
              let val = parseFloat(v.valor);
              if (isPuro.value) val = val > 0 ? 1 : 0;
              else if (val > 60) val = 60;
              return [v.fecha_hora_lectura, val];
          }),
          itemStyle: { color: '#8A2BE2' },
          lineStyle: { width: 2 },
          areaStyle: { color: 'rgba(138, 43, 226, 0.1)' }
        });
      }
    });

    if (dataFound && statsEmit) {
      emit('estadisticas', {
        id: props.campos[0].id,
        nombre: props.campos[0].nombre,
        unidad: '% Ocup.',
        min: 0,
        max: 100,
        avg: statsEmit.avg,
        es_texto: false,
        claseColor: 'text-primary'
      });
      updateChartOptions(allSeries, yAxis);
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

const updateChartOptions = (series, yAxis) => {
  chartOption.value = {
    title: { text: 'Patrones de Ocupación', left: 'center', textStyle: { color: textColor.value } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, backgroundColor: tooltipBgColor.value, textStyle: { color: textColor.value } },
    legend: { textStyle: { color: textColor.value }, bottom: 20 },
    toolbox: { show: true, feature: { magicType: { type: ['line', 'bar'], title: { line: 'Línea', bar: 'Barras' } }, saveAsImage: { show: true, title: 'Exportar' } }, iconStyle: { borderColor: textColor.value } },
    grid: { left: 50, right: 30, bottom: 65, top: 50, containLabel: true },
    xAxis: { type: 'time', axisLine: { lineStyle: { color: gridColor.value } }, axisLabel: { color: textColor.value } },
    yAxis: yAxis,
    dataZoom: [{ type: 'slider', bottom: 5, textStyle: { color: textColor.value }, height: 16 }, { type: 'inside' }],
    series: series
  };
};

watch(() => [camposIdsStr.value, props.fechaInicio, props.fechaFin, props.metodoCarga], cargarDatosCombinados, { immediate: true });
watch(() => props.isDark, () => { if (hasData.value) updateChartOptions(chartOption.value.series, chartOption.value.yAxis); });

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
.spinner { border: 4px solid rgba(0, 0, 0, 0.1); border-left-color: #8A2BE2; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 10px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.error-message i, .no-data-message i { margin-right: 8px; font-size: 1.3em; }
.error-message { color: #E74C3C; }
.no-data-message { color: #8A2BE2; }
.updating-badge { position: absolute; top: 10px; right: 10px; background: rgba(138, 43, 226, 0.9); color: white; padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; z-index: 5; }
</style>