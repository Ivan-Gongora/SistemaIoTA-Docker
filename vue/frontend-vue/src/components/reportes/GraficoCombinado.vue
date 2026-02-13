<template>
  <div class="grafico-combinado-container" :class="{ 'theme-dark': isDark }">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Cargando datos históricos...</p>
    </div>
    <div v-else-if="error" class="error-message">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
    </div>
    <div v-else-if="!hasData" class="no-data-message">
      <i class="bi bi-info-circle-fill"></i> No hay datos disponibles para el rango seleccionado.
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
  ToolboxComponent, // Agregado para posibles funciones como guardar imagen
} from 'echarts/components';
import VChart from 'vue-echarts';
import { ref, watch, computed, onMounted } from 'vue';

// Registro de componentes de ECharts
use([
  CanvasRenderer, LineChart, TitleComponent, TooltipComponent, 
  LegendComponent, GridComponent, DataZoomComponent, ToolboxComponent
]);

// const API_BASE_URL = 'http://127.0.0.1:8001'; // Asegúrate de que esta URL sea correcta

const props = defineProps({
  campos: {
    type: Array,
    required: true,
    // Debería ser un array de objetos con { id, nombre, unidad: { simbolo, magnitud_tipo } }
  },
  fechaInicio: { type: String, required: true }, // ISO String
  fechaFin: { type: String, required: true },   // ISO String
  isDark: { type: Boolean, default: false }
});

const loading = ref(true);
const error = ref(null);
const chartOption = ref({});
const hasData = ref(false); // Para controlar si hay datos para mostrar
const seriesColors = ['#8A2BE2', '#1ABC9C', '#3498DB', '#E74C3C', '#F1C40F', '#9B59B6', '#2ECC71', '#E67E22', '#16A085', '#D35400'];

const gridColor = computed(() => props.isDark ? 'rgba(228, 230, 235, 0.2)' : 'rgba(51, 51, 51, 0.2)');
const textColor = computed(() => props.isDark ? '#E4E6EB' : '#333333');
const legendTextColor = computed(() => props.isDark ? '#E4E6EB' : '#333333'); // Color para la leyenda
const tooltipBgColor = computed(() => props.isDark ? 'rgba(51, 51, 51, 0.8)' : 'rgba(255, 255, 255, 0.9)');
const tooltipTextColor = computed(() => props.isDark ? '#E4E6EB' : '#333333');


// Función para cargar los datos de UN SOLO campo
const fetchCampoData = async (campo) => {
  const token = localStorage.getItem('accessToken');
  const url = new URL(`${API_BASE_URL}/api/valores/historico-campo/${campo.id}`);
  url.searchParams.append('fecha_inicio', props.fechaInicio);
  url.searchParams.append('fecha_fin', props.fechaFin);

  try {
    const response = await fetch(url.toString(), {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || `Fallo al cargar datos para ${campo.nombre}.`);
    }
    return await response.json();
  } catch (err) {
    console.error(`Error al cargar datos para el campo ${campo.nombre}:`, err.message);
    return []; // Retorna un array vacío en caso de error para no detener los demás
  }
};

// Función principal para cargar y combinar todos los datos
const cargarDatosCombinados = async () => {
  loading.value = true;
  error.value = null;
  hasData.value = false;
  chartOption.value = {}; // Reiniciar opciones del gráfico

  if (!props.campos || props.campos.length === 0) {
    loading.value = false;
    error.value = 'No hay campos seleccionados para graficar.';
    return;
  }
  if (!props.fechaInicio || !props.fechaFin) {
    loading.value = false;
    error.value = 'Rango de fechas no válido.';
    return;
  }

  try {
    const allSeries = [];
    const allYAxes = [];
    const uniqueMagnitudes = new Set(); // Para asegurar un eje Y por magnitud

    // Promesas para cargar todos los datos en paralelo
    const dataPromises = props.campos.map(campo => fetchCampoData(campo));
    const results = await Promise.all(dataPromises);

    results.forEach((valores, index) => {
      const campo = props.campos[index];
      if (valores.length > 0) {
        hasData.value = true;
        
        const magnitud = campo.unidad?.magnitud_tipo || 'Valor';
        const simbolo = campo.unidad?.simbolo || '';
        const seriesName = `${campo.nombre} (${simbolo})`;

        // Si esta magnitud no tiene un eje Y asignado, crearlo
        if (!uniqueMagnitudes.has(magnitud)) {
          uniqueMagnitudes.add(magnitud);
          allYAxes.push({
            type: 'value',
            name: `${magnitud} (${simbolo})`,
            nameLocation: 'middle',
            nameGap: 50, // Ajusta esto si el nombre se superpone
            position: allYAxes.length % 2 === 0 ? 'left' : 'right', // Alternar posición para más de 2 ejes
            offset: allYAxes.length > 1 ? (allYAxes.length - 1) * 60 : 0, // Separar ejes
            axisLine: {
              show: true,
              lineStyle: { color: seriesColors[allSeries.length % seriesColors.length] } // Color del eje según la serie
            },
            axisLabel: {
              color: textColor.value,
              formatter: `{value} ${simbolo}`
            },
            splitLine: { show: false }, // Desactivar líneas de división para ejes secundarios
            min: 'dataMin', // Ajustar automáticamente
            max: 'dataMax'
          });
        }
        
        // Encontrar el índice del eje Y para esta magnitud
        const yAxisIndex = Array.from(uniqueMagnitudes).indexOf(magnitud);

        allSeries.push({
          name: seriesName,
          type: 'line',
          yAxisIndex: yAxisIndex, // Asignar al eje Y correspondiente
          data: valores.map(v => [v.fecha_hora_lectura, parseFloat(v.valor)]),
          showSymbol: false,
          smooth: true,
          lineStyle: {
            width: 2,
            color: seriesColors[allSeries.length % seriesColors.length] // Color de la línea
          }
        });
      }
    });

    if (!hasData.value) {
        error.value = 'No hay datos para los campos seleccionados en este rango de fechas.';
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
    title: {
      text: 'Gráfico Combinado de Datos Históricos',
      left: 'center',
      textStyle: {
        color: textColor.value
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: { backgroundColor: '#6a7985' }
      },
      backgroundColor: tooltipBgColor.value,
      textStyle: {
          color: tooltipTextColor.value
      },
      // Formatear el tooltip para mostrar los valores de cada eje
      formatter: function (params) {
          let html = `${params[0].name}<br/>`; // Fecha
          params.forEach(item => {
              html += `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${item.color};"></span>
                       ${item.seriesName}: ${item.value[1]}<br/>`;
          });
          return html;
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 40,
      textStyle: {
        color: legendTextColor.value
      }
    },
    grid: {
      left: 100, // Espacio para ejes Y izquierdos
      right: 100, // Espacio para ejes Y derechos
      bottom: 70,
      top: 80,
      containLabel: true // Asegura que las etiquetas del eje Y no se corten
    },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: gridColor.value } },
      axisLabel: { color: textColor.value }
    },
    yAxis: yAxes.length > 0 ? yAxes : [{ type: 'value', axisLabel: { color: textColor.value }, splitLine: { lineStyle: { color: gridColor.value } } }], // Fallback para un eje si no hay ninguno
    dataZoom: [
      {
        type: 'slider',
        start: 0,
        end: 100,
        bottom: 10,
        height: 25,
        backgroundColor: props.isDark ? 'rgba(43, 43, 64, 0.5)' : 'rgba(255, 255, 255, 0.5)',
        borderColor: gridColor.value,
        textStyle: { color: textColor.value }
      },
      {
        type: 'inside'
      }
    ],
    series: series
  };
};

// --- WATCHERS ---
watch(
  () => [props.campos, props.fechaInicio, props.fechaFin],
  cargarDatosCombinados,
  { immediate: true, deep: true }
);

watch(
  () => props.isDark,
  () => {
    // Si cambia el tema, recargar las opciones para actualizar colores
    if (hasData.value) { // Solo si hay datos para evitar errores si está vacío
      cargarDatosCombinados();
    }
  }
);

onMounted(() => {
  // Asegurarse de cargar los datos al montar si ya hay props
  if (props.campos.length > 0 && props.fechaInicio && props.fechaFin) {
    cargarDatosCombinados();
  }
});
</script>

<style scoped>
.grafico-combinado-container {
  position: relative;
  width: 100%;
  height: 500px; /* 🚨 CRÍTICO: Establece una altura fija o flexible */
  background-color: #FFFFFF; /* Fondo claro por defecto */
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  display: flex; /* Para centrar mensajes */
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.grafico-combinado-container.theme-dark {
  background-color: #2B2B40; /* Fondo oscuro */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.chart {
  width: 100%;
  height: 100%; /* El gráfico ocupará toda la altura del contenedor */
}

.loading-overlay, .error-message, .no-data-message {
  position: absolute; /* Para que esté por encima del gráfico, si se renderiza */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.8); /* Fondo semitransparente */
  border-radius: 12px;
  z-index: 10; /* Asegurar que esté por encima del gráfico base */
  color: #333;
  font-size: 1.1rem;
}

.grafico-combinado-container.theme-dark .loading-overlay,
.grafico-combinado-container.theme-dark .error-message,
.grafico-combinado-container.theme-dark .no-data-message {
    background-color: rgba(43, 43, 64, 0.9);
    color: #E4E6EB;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #8A2BE2;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message i, .no-data-message i {
  margin-right: 8px;
  font-size: 1.3em;
}
.error-message { color: #e74c3c; }
.no-data-message { color: #3498DB; }
</style>