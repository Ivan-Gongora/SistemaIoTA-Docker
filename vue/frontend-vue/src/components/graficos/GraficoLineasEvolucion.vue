<template>
  <div class="chart-card" :class="{ 'theme-dark': isDark }">
    <div class="card-header-actions">
      <div class="titles">
        <h5 class="card-title">{{ titulo }}</h5>
        <h6 class="card-subtitle" v-if="subtitulo">{{ subtitulo }}</h6>
      </div>
      <button class="btn-download" @click="descargarGrafico" title="Descargar imagen">
        <i class="bi bi-download"></i>
      </button>
    </div>
    
    <div class="chart-container">
      <v-chart 
        ref="mixedChart" 
        class="chart" 
        :option="chartOption" 
        autoresize 
        :style="{ height: '100%', minHeight: '350px' }"
      />
    </div>
  </div>
</template>

<script>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components';
import VChart from 'vue-echarts';

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent,
  ToolboxComponent
]);

export default {
  name: 'GraficoLineasEvolucion',
  components: {
    VChart,
  },
  props: {
    titulo: { type: String, default: 'Patrón Mensual' },
    subtitulo: { type: String, default: '' },
    // Estructura esperada: [ { name: 'Consumo (kWh)', data: [{mes:1, ...}, ...] }, { name: 'Costo (MXN)', ... } ]
    datosMensuales: {
      type: Array,
      required: true,
    },
    isDark: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      chartOption: {},
      mesesNombres: [
        'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
      ]
    };
  },
  watch: {
    datosMensuales: { handler: 'crearChartOption', deep: true },
    isDark: 'crearChartOption',
  },
  mounted() {
    this.crearChartOption();
  },
  methods: {
    crearChartOption() {
      if (!this.datosMensuales || this.datosMensuales.length === 0) {
        this.chartOption = {};
        return;
      }

      // 1. Extraer Series (Consumo vs Costo)
      const serieConsumo = this.datosMensuales.find(s => s.name.includes('Consumo'));
      const serieCosto = this.datosMensuales.find(s => s.name.includes('Costo'));

      if (!serieConsumo || !serieCosto) return;

      // 2. Mapear datos a Arrays simples
      // Asumimos que los datos vienen ordenados por mes (1 a 12), si no, habría que ordenar.
      const consumoData = serieConsumo.data.map(d => d.consumo_total_kwh || 0);
      const costoData = serieCosto.data.map(d => d.costo_total || 0);
      
      // Usamos los meses nombres como categorías
      const categorias = this.mesesNombres;

      // 3. Estilos y Colores
      const textColor = this.isDark ? '#E0E0E0' : '#333333';
      const axisColor = this.isDark ? '#A0A0A0' : '#666666';
      const splitLineColor = this.isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
      
      const colorConsumo = '#8A2BE2'; // Morado
      const colorCosto = '#00C853';   // Verde

      this.chartOption = {
        backgroundColor: 'transparent',
        
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', crossStyle: { color: '#999' } },
          backgroundColor: this.isDark ? 'rgba(40, 40, 60, 0.95)' : 'rgba(255, 255, 255, 0.95)',
          borderColor: this.isDark ? '#444' : '#DDD',
          textStyle: { color: textColor },
          formatter: (params) => {
            let tooltip = `<div style="margin-bottom: 5px; font-weight: bold; border-bottom: 1px solid ${axisColor}; padding-bottom: 3px;">${params[0].name}</div>`;
            params.forEach(item => {
              let val = Number(item.value).toLocaleString('es-MX', { maximumFractionDigits: 2 });
              let unit = item.seriesName.includes('Consumo') ? 'kWh' : 'MXN';
              tooltip += `
                <div style="display: flex; justify-content: space-between; gap: 15px; margin-top: 4px;">
                  <span style="color: ${item.color}">● ${item.seriesName}</span>
                  <span style="font-weight: bold">${val} ${unit}</span>
                </div>`;
            });
            return tooltip;
          }
        },
        
        legend: {
          data: ['Consumo (kWh)', 'Costo (MXN)'],
          bottom: 0,
          textStyle: { color: textColor }
        },
        
        grid: {
          left: '3%',
          right: '3%',
          bottom: '12%',
          top: '15%',
          containLabel: true
        },
        
        xAxis: [
          {
            type: 'category',
            data: categorias,
            axisPointer: { type: 'shadow' },
            axisLabel: { color: textColor },
            axisLine: { lineStyle: { color: axisColor } }
          }
        ],
        
        // DOBLE EJE Y
        yAxis: [
          {
            type: 'value',
            name: 'Consumo',
            min: 0,
            position: 'left',
            axisLabel: { formatter: '{value} k', color: colorConsumo },
            axisLine: { show: true, lineStyle: { color: colorConsumo } },
            splitLine: { lineStyle: { type: 'dashed', color: splitLineColor } }
          },
          {
            type: 'value',
            name: 'Costo',
            min: 0,
            position: 'right',
            axisLabel: { formatter: '${value}', color: colorCosto },
            axisLine: { show: true, lineStyle: { color: colorCosto } },
            splitLine: { show: false }
          }
        ],
        
        series: [
          {
            name: 'Consumo (kWh)',
            type: 'bar',
            data: consumoData,
            yAxisIndex: 0, // Usa eje izquierdo
            itemStyle: { 
                color: {
                    type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [{ offset: 0, color: '#8A2BE2' }, { offset: 1, color: '#6A1B9A' }]
                },
                borderRadius: [4, 4, 0, 0]
            },
            barMaxWidth: 40
          },
          {
            name: 'Costo (MXN)',
            type: 'line',
            data: costoData,
            yAxisIndex: 1, // Usa eje derecho
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: { color: colorCosto, borderColor: '#fff', borderWidth: 2 },
            lineStyle: { width: 3, color: colorCosto }
          }
        ]
      };
    },

    descargarGrafico() {
      const chartInstance = this.$refs.mixedChart;
      if (!chartInstance) return;

      const url = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: this.isDark ? '#2B2B40' : '#FFFFFF'
      });

      const link = document.createElement('a');
      link.href = url;
      link.download = `Patron_Mensual_${new Date().toISOString().slice(0,10)}.png`;
      link.click();
    }
  },
};
</script>

<style scoped lang="scss">
.chart-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;

  .titles {
    display: flex;
    flex-direction: column;
    
    .card-title {
      margin: 0;
      font-size: 1rem;
      font-weight: 700;
      color: inherit;
    }
    .card-subtitle {
      margin: 2px 0 0 0;
      font-size: 0.8rem;
      opacity: 0.7;
    }
  }

  .btn-download {
    background: transparent;
    border: none;
    color: #99A2AD;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;

    &:hover {
      color: #8A2BE2;
      background-color: rgba(138, 43, 226, 0.1);
    }
  }
}

.chart-container {
  flex-grow: 1;
  min-height: 0;
  position: relative;
}
</style>