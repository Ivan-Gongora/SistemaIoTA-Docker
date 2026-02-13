<template>
  <div class="chart-card" :class="{ 'theme-dark': isDark }">
    <div class="card-body">
      <v-chart class="chart" :option="chartOption" autoresize />
    </div>
  </div>
</template>

<script>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  GridComponent, TooltipComponent, LegendComponent, DataZoomComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';

// Registrar los componentes de ECharts
use([
  CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent
]);

export default {
  name: 'GraficoSimulacionECharts',
  components: { VChart },
  props: {
    chartData: {
      type: Object,
      required: true,
    },
    isDark: Boolean,
  },
  data() {
    return { chartOption: {} };
  },
  watch: {
    chartData: { handler: 'crearChartOption', deep: true },
    isDark: 'crearChartOption',
  },
  mounted() {
    this.crearChartOption();
  },
  methods: {
    crearChartOption() {
      const datosCompletos = this.chartData;

      if (!datosCompletos || !datosCompletos.datos_historicos_usados || !datosCompletos.predicciones_escenario) {
        this.chartOption = {};
        return;
      }
      
      const historico = datosCompletos.datos_historicos_usados;
      const proyeccion = datosCompletos.predicciones_escenario;
      const historicoLength = historico.length;
      
      // 1. Preparar Etiquetas (X-Axis)
      const labels = [
        ...historico.map(d => d.periodo.slice(0, 7)),
        ...proyeccion.map(d => d.periodo.slice(0, 7))
      ];
      
      // 2. Preparar Datos de Consumo
      // Consumo Real (histórico)
      const datosReales = historico.map(d => d.consumo_total_kwh);
      
      // Consumo Base Proyectado
      const datosBaseProyectado = proyeccion.map(d => d.consumo_base_kwh);
      
      // Consumo Escenario Simulado
      const datosSimulado = proyeccion.map(d => d.consumo_escenario_kwh);

      // 3. Definir series para ECharts
      
      // Serie 1: Consumo Base
      // Combinamos datos: Histórico REAL + Proyección BASE
      const serieBase = [
        // Datos Reales
        ...datosReales.slice(0, historicoLength), 
        // Proyección Base
        ...datosBaseProyectado
      ];
      
      // Serie 2: Consumo Simulado
      // Combinamos datos: Nulls en histórico + Proyección SIMULADA
      const serieSimulado = [
        // Rellenar el histórico con null para que la línea simulada empiece en la proyección
        ...Array(historicoLength).fill(null),
        // Proyección Simulado
        ...datosSimulado
      ];

      // 4. Configuración de Estilos
      const textColor = this.isDark ? '#E4E6EB' : '#333333';
      const axisColor = this.isDark ? '#99A2AD' : '#555555';
      const gridLineColor = this.isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
      
      // Colores de línea
      const colorBase = this.isDark ? '#6A5ACD' : '#3399CC'; // Azul/Morado claro para Base
      const colorSimulado = '#8A2BE2'; // Morado Principal

      // 5. Configuración ECharts
      this.chartOption = {
        color: [colorBase, colorSimulado],
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            let tooltipContent = `<b>Periodo: ${params[0].name}</b><br/>`;
            params.forEach((item, index) => {
              if (item.value !== null) {
                const value = item.value;
                const isReal = item.dataIndex < historicoLength;
                const seriesName = isReal && item.seriesName === 'Consumo Base Proyectado' 
                    ? 'Consumo Histórico REAL' 
                    : item.seriesName;
                const lineStyle = isReal ? 'SÓLIDA - Real' : 'PUNTEADA - Proyectado'; // Etiqueta para el usuario
                
                tooltipContent += `${item.marker} ${seriesName}: <b>${value.toLocaleString('es-MX', { maximumFractionDigits: 0 })} kWh</b> (${lineStyle})<br/>`;
              }
            });
            return tooltipContent;
          },
          backgroundColor: this.isDark ? 'rgba(43,43,64,0.85)' : 'rgba(255,255,255,0.85)',
          textStyle: { color: textColor },
        },
        legend: {
          data: ['Consumo Base Proyectado', 'Consumo Escenario Simulado'],
          textStyle: { color: textColor },
          top: 30,
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '20%',
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: labels,
          boundaryGap: false,
          axisLabel: { color: axisColor, rotate: 45 },
          axisLine: { lineStyle: { color: axisColor } },
          splitLine: { show: false },
        },
        yAxis: {
          type: 'value',
          name: 'Consumo Total (kWh)',
          axisLabel: { formatter: (value) => value.toLocaleString('es-MX', { maximumFractionDigits: 0 }) + ' kWh', color: axisColor },
          axisLine: { lineStyle: { color: axisColor } },
          splitLine: { lineStyle: { color: gridLineColor } },
        },
        series: [
          {
            name: 'Consumo Base Proyectado', 
            type: 'line',
            data: serieBase.map((value, index) => ({
                value: value,
                // Usamos un styleFunction para cambiar el tipo de línea
                itemStyle: {
                    color: colorBase
                },
                lineStyle: {
                    type: index < historicoLength ? 'solid' : 'dashed', // Sólida para Histórico, Punteada para Proyección Base
                    width: 2,
                    color: colorBase
                }
            })),
            smooth: true,
            showSymbol: false, // Ocultar símbolos para una línea más limpia
          },
          {
            name: 'Consumo Escenario Simulado', 
            type: 'line',
            data: serieSimulado.map(value => ({
                value: value,
                lineStyle: {
                    type: 'solid', // Línea simulada siempre sólida
                    width: 4
                },
                itemStyle: {
                    color: colorSimulado
                }
            })),
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 4, color: colorSimulado }, 
            itemStyle: { color: colorSimulado },
            areaStyle: {
              opacity: 0.3,
              color: colorSimulado
            },
          }
        ],
        backgroundColor: 'transparent',
        dataZoom: [{ type: 'slider', xAxisIndex: 0, start: 0, end: 100, textStyle: { color: axisColor } }, { type: 'inside', xAxisIndex: 0, start: 0, end: 100 }],
      };
    },
  },
};
</script>

<style scoped>
/* Estilos necesarios para que la card se vea bien en esta vista */
.chart-card {
  height: 100%;
  min-height: 450px; 
  display: flex;
  flex-direction: column;
  background-color: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: 0 4px 10px var(--shadow-color);
  padding: 1.5rem;
}
.chart-card .card-title {
  color: var(--text-color-primary);
  font-size: 1.35rem; 
  margin-bottom: 1.5rem;
  text-align: left;
  font-weight: 600;
}
.chart {
  flex-grow: 1;
  min-height: 350px;
}
</style>