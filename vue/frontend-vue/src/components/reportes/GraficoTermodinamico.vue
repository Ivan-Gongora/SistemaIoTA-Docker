<template>
  <div class="grafico-combinado-container" :class="{ 'theme-dark': isDark }">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Extrayendo datos de clima...</p>
    </div>
    <div v-else-if="error" class="error-message">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
    </div>
    <div v-else-if="!hasData" class="no-data-message">
      <i class="bi bi-info-circle-fill"></i> Sin registros termodinámicos en este periodo.
    </div>
    <VChart v-else :option="chartOption" class="chart" autoresize />
  </div>
</template>

<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent
} from 'echarts/components';
import VChart from 'vue-echarts';
import { ref, watch, computed, onMounted } from 'vue';

use([
  CanvasRenderer, LineChart, TitleComponent, TooltipComponent, 
  LegendComponent, GridComponent, DataZoomComponent, ToolboxComponent, MarkLineComponent
]);

const props = defineProps({
  campos: { type: Array, required: true },
  fechaInicio: { type: String, required: true },
  fechaFin: { type: String, required: true },
  isDark: { type: Boolean, default: false },
  limites: { type: Object, default: () => ({ tempMin: 20, tempMax: 26, humMin: 30, humMax: 65 }) }
});

const loading = ref(true);
const error = ref(null);
const chartOption = ref({});
const hasData = ref(false);

const gridColor = computed(() => props.isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)');
const textColor = computed(() => props.isDark ? '#E4E6EB' : '#333333');
const tooltipBgColor = computed(() => props.isDark ? '#1a1d2d' : '#ffffff');

const baseUrlAPI = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8001';

const fetchCampoData = async (campo) => {
  const token = localStorage.getItem('accessToken');
  const url = new URL(`${baseUrlAPI}/api/valores/historico-campo/${campo.id}`);
  url.searchParams.append('fecha_inicio', props.fechaInicio);
  url.searchParams.append('fecha_fin', props.fechaFin);

  try {
    const response = await fetch(url.toString(), {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || `Fallo al cargar ${campo.nombre}.`);
    }
    return await response.json();
  } catch (err) {
    console.error(`Error en campo ${campo.nombre}:`, err.message);
    return [];
  }
};

const cargarDatosCombinados = async () => {
  loading.value = true;
  error.value = null;
  hasData.value = false;
  chartOption.value = {};

  const camposTermo = props.campos.filter(c => {
    const n = c.nombre.toLowerCase();
    return n.includes('temperatura') || n.includes('humedad');
  });

  if (camposTermo.length === 0) {
    loading.value = false;
    error.value = 'Selecciona métricas de temperatura o humedad.';
    return;
  }

  try {
    const allSeries = [];
    const allYAxes = [
      {
        type: 'value',
        name: 'Temperatura (°C)',
        position: 'left',
        axisLine: { show: true, lineStyle: { color: '#ef4444' } },
        axisLabel: { color: textColor.value, formatter: '{value}°' },
        splitLine: { lineStyle: { color: gridColor.value } }
      },
      {
        type: 'value',
        name: 'Humedad (%)',
        position: 'right',
        axisLine: { show: true, lineStyle: { color: '#0ea5e9' } },
        axisLabel: { color: textColor.value, formatter: '{value}%' },
        splitLine: { show: false }
      }
    ];

    const dataPromises = camposTermo.map(campo => fetchCampoData(campo));
    const results = await Promise.all(dataPromises);

    results.forEach((valores, index) => {
      const campo = camposTermo[index];
      if (valores.length > 0) {
        hasData.value = true;
        const n = campo.nombre.toLowerCase();
        const isTemp = n.includes('temperatura');
        const colorSerie = isTemp ? '#ef4444' : '#0ea5e9';
        
        const markLineData = [];
        if (isTemp) {
            markLineData.push({ yAxis: props.limites.tempMin, name: 'Min', lineStyle: { color: '#ef4444', type: 'dashed' } });
            markLineData.push({ yAxis: props.limites.tempMax, name: 'Max', lineStyle: { color: '#ef4444', type: 'dashed' } });
        } else {
            markLineData.push({ yAxis: props.limites.humMax, name: 'Max', lineStyle: { color: '#0ea5e9', type: 'dashed' } });
        }

        allSeries.push({
          name: campo.nombre,
          type: 'line',
          yAxisIndex: isTemp ? 0 : 1,
          data: valores.map(v => [v.fecha_hora_lectura, parseFloat(v.valor)]),
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 3, color: colorSerie },
          itemStyle: { color: colorSerie },
          areaStyle: isTemp ? null : { color: 'rgba(14, 165, 233, 0.2)' },
          markLine: { data: markLineData, symbol: 'none' }
        });
      }
    });

    if (!hasData.value) {
      error.value = 'Registros vacíos en el servidor.';
    }

    updateChartOptions(allSeries, allYAxes);

  } catch (err) {
    error.value = err.message;
    hasData.value = false;
  } finally {
    loading.value = false;
  }
};

const updateChartOptions = (series, yAxes) => {
  chartOption.value = {
    title: { text: 'Termodinámica Integrada', left: 'center', textStyle: { color: textColor.value } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: tooltipBgColor.value,
      textStyle: { color: textColor.value }
    },
    legend: { data: series.map(s => s.name), bottom: 0, textStyle: { color: textColor.value } },
    toolbox: { show: true, feature: { saveAsImage: { show: true, title: 'Exportar' } }, iconStyle: { borderColor: textColor.value } },
    grid: { left: 60, right: 60, bottom: 60, top: 60 },
    xAxis: { type: 'time', axisLine: { lineStyle: { color: gridColor.value } }, axisLabel: { color: textColor.value } },
    yAxis: yAxes,
    dataZoom: [
      { type: 'slider', bottom: 30, textStyle: { color: textColor.value } },
      { type: 'inside' }
    ],
    series: series
  };
};

watch(() => [props.campos, props.fechaInicio, props.fechaFin], cargarDatosCombinados, { immediate: true, deep: true });
watch(() => props.isDark, () => { if (hasData.value) cargarDatosCombinados(); });
onMounted(() => { if (props.campos.length > 0) cargarDatosCombinados(); });
</script>

<style scoped>
.grafico-combinado-container { position: relative; width: 100%; height: 450px; background-color: #FFFFFF; border-radius: 16px; border: 1px solid rgba(0, 0, 0, 0.05); display: flex; align-items: center; justify-content: center; flex-direction: column; overflow: hidden; margin-bottom: 24px; }
.grafico-combinado-container.theme-dark { background-color: #161925; border-color: rgba(255, 255, 255, 0.05); }
.chart { width: 100%; height: 100%; }
.loading-overlay, .error-message, .no-data-message { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: rgba(255, 255, 255, 0.8); z-index: 10; color: #333; font-size: 1.1rem; }
.grafico-combinado-container.theme-dark .loading-overlay, .grafico-combinado-container.theme-dark .error-message, .grafico-combinado-container.theme-dark .no-data-message { background-color: rgba(22, 25, 37, 0.9); color: #E4E6EB; }
.spinner { border: 4px solid rgba(0, 0, 0, 0.1); border-left-color: #ef4444; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 10px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.error-message i, .no-data-message i { margin-right: 8px; font-size: 1.3em; }
.error-message { color: #ef4444; }
.no-data-message { color: #3b82f6; }
</style>