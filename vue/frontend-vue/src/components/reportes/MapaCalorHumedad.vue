<template>
  <div class="grafico-combinado-container" :class="{ 'theme-dark': isDark }">
    <div v-if="loading && !hasData" class="loading-overlay">
      <div class="spinner"></div>
      <p>Construyendo matriz de humedad...</p>
    </div>
    <div v-else-if="error" class="error-message">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
    </div>
    <div v-else-if="!hasData && !loading" class="no-data-message">
      <i class="bi bi-info-circle-fill"></i> Sin registros de humedad suficientes.
    </div>
    <VChart v-show="hasData && !error" :option="chartOption" class="chart" autoresize />
    <div v-if="loading && hasData" class="updating-badge">Actualizando...</div>
  </div>
</template>

<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { HeatmapChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, VisualMapComponent, ToolboxComponent, DataZoomComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { ref, watch, computed, onBeforeUnmount } from 'vue';

use([CanvasRenderer, HeatmapChart, TitleComponent, TooltipComponent, GridComponent, VisualMapComponent, ToolboxComponent, DataZoomComponent]);

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

const gridColor = computed(() => props.isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)');
const textColor = computed(() => props.isDark ? '#E4E6EB' : '#333333');
const tooltipBgColor = computed(() => props.isDark ? '#2B2B40' : '#ffffff');
const borderColor = computed(() => props.isDark ? '#2B2B40' : '#ffffff');
const camposIdsStr = computed(() => props.campos.map(c => c.id).join(','));

const extraerEstadisticasSeguras = (valores) => {
  if (Array.isArray(valores) && valores.length > 0 && valores[0]?.estadisticas_globales) {
    return valores[0].estadisticas_globales;
  }
  let sum = 0, count = 0, min = Infinity, max = -Infinity;
  if (Array.isArray(valores)) {
    valores.forEach(v => {
        let val = parseFloat(v.valor);
        if (!isNaN(val) && v.valor !== null && v.valor !== '') {
            sum += val; count++;
            if (val < min) min = val;
            if (val > max) max = val;
        }
    });
  }
  return { min: count > 0 ? min : null, max: count > 0 ? max : null, avg: count > 0 ? sum / count : null };
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

const cargarMapaCalor = async () => {
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
    const response = await fetchCampoData(props.campos[0], signal);
    const stats = extraerEstadisticasSeguras(response);

    const valoresValidos = Array.isArray(response) ? response.filter(v => v.valor !== null && v.valor !== '' && !isNaN(parseFloat(v.valor))) : [];

    if (valoresValidos.length > 0) {
      emit('estadisticas', {
        id: props.campos[0].id,
        nombre: props.campos[0].nombre,
        unidad: '%',
        min: stats.min !== null ? parseFloat(stats.min).toFixed(1) : '-',
        max: stats.max !== null ? parseFloat(stats.max).toFixed(1) : '-',
        avg: stats.avg !== null ? parseFloat(stats.avg).toFixed(1) : '-',
        es_texto: false,
        claseColor: 'text-info'
      });

      const uniqueDates = [];
      const heatmapData = [];
      const horasY = Array.from({ length: 24 }, (_, i) => `${i}:00`);

      const procesados = valoresValidos.map(v => {
          let fecha = '';
          let hora = 0;
          const str = String(v.fecha_hora_lectura);
          
          if (str.includes('T')) {
              const parts = str.split('T');
              fecha = parts[0];
              hora = parseInt(parts[1].split(':')[0], 10);
          } else if (str.includes(' ')) {
              const parts = str.split(' ');
              fecha = parts[0];
              hora = parseInt(parts[1].split(':')[0], 10);
          } else {
              fecha = str;
          }

          return { fecha, hora, valor: parseFloat(v.valor) };
      });

      procesados.forEach(item => { if (!uniqueDates.includes(item.fecha)) uniqueDates.push(item.fecha); });
      uniqueDates.sort();

      procesados.forEach(item => {
          const xIndex = uniqueDates.indexOf(item.fecha);
          const yIndex = item.hora; 
          heatmapData.push([xIndex, yIndex, parseFloat(item.valor.toFixed(1))]);
      });

      updateChartOptions(uniqueDates, horasY, heatmapData);
      hasData.value = true;
    } else {
      hasData.value = false;
      error.value = 'Registros insuficientes para el mapeo.';
    }
  } catch (err) {
    if (err.name === 'AbortError') return;
    error.value = err.message;
    hasData.value = false;
  } finally {
    if (!signal.aborted) loading.value = false;
  }
};

const updateChartOptions = (dates, hours, data) => {
  const spanDias = 10;
  const endZoom = dates.length > spanDias ? Math.floor((spanDias / dates.length) * 100) : 100;

  chartOption.value = {
    title: { text: 'Matriz de Calor: Humedad', left: 'center', textStyle: { color: textColor.value } },
    tooltip: { position: 'top', formatter: (params) => `${dates[params.value[0]]} ${hours[params.value[1]]}<br/><b>${params.value[2]} %</b>`, backgroundColor: tooltipBgColor.value, textStyle: { color: textColor.value } },
    toolbox: { show: true, feature: { saveAsImage: { show: true, title: 'Exportar' } }, iconStyle: { borderColor: textColor.value } },
    grid: { top: 60, bottom: 130, left: 60, right: 30 },
    xAxis: { type: 'category', data: dates, splitArea: { show: true }, axisLabel: { color: textColor.value }, axisLine: { lineStyle: { color: gridColor.value } } },
    yAxis: { type: 'category', data: hours, splitArea: { show: true }, axisLabel: { color: textColor.value, interval: 0, fontSize: 11 }, axisLine: { lineStyle: { color: gridColor.value } } },
    dataZoom: [
      { type: 'slider', bottom: 70, start: 0, end: endZoom, height: 16, textStyle: { color: textColor.value } },
      { type: 'inside' }
    ],
    visualMap: {
        min: 0,
        max: 100,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 10,
        itemWidth: 15,
        itemHeight: 300,
        textStyle: { color: textColor.value },
        inRange: { color: ['#F7FBFF', '#C6DBEF', '#6BAED6', '#2171B5', '#08306B'] } 
    },
    series: [{
        name: 'Humedad',
        type: 'heatmap',
        data: data,
        label: { show: true, fontSize: 10, fontWeight: 'bold' },
        itemStyle: { borderColor: borderColor.value, borderWidth: 2 },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  };
};

watch(() => [camposIdsStr.value, props.fechaInicio, props.fechaFin, props.metodoCarga], cargarMapaCalor, { immediate: true });
watch(() => props.isDark, () => { if (hasData.value) updateChartOptions(chartOption.value.xAxis.data, chartOption.value.yAxis.data, chartOption.value.series[0].data); });

onBeforeUnmount(() => {
  if (abortController) abortController.abort();
});
</script>

<style scoped>
.grafico-combinado-container { position: relative; width: 100%; height: 560px; background-color: #FFFFFF; border-radius: 12px; border: 1px solid rgba(0, 0, 0, 0.05); display: flex; align-items: center; justify-content: center; flex-direction: column; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
.grafico-combinado-container.theme-dark { background-color: #2B2B40; border-color: #3C3C55; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
.chart { width: 100%; height: 100%; padding: 12px; }
.loading-overlay, .error-message, .no-data-message { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: rgba(255, 255, 255, 0.8); z-index: 10; font-weight: 700; color: #333; padding: 20px; text-align: center; }
.grafico-combinado-container.theme-dark .loading-overlay, .grafico-combinado-container.theme-dark .error-message, .grafico-combinado-container.theme-dark .no-data-message { background-color: rgba(43, 43, 64, 0.9); color: #E4E6EB; }
.spinner { border: 4px solid rgba(0, 0, 0, 0.1); border-left-color: #3498DB; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 10px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.error-message i, .no-data-message i { margin-right: 8px; font-size: 1.3em; }
.error-message { color: #E74C3C; }
.no-data-message { color: #3498DB; }
.updating-badge { position: absolute; top: 10px; right: 10px; background: rgba(52, 152, 219, 0.9); color: white; padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; z-index: 5; }
</style>