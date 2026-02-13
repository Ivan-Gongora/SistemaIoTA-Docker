<template>
  <div class="chart-card" :class="{ 'theme-dark': isDark }">
    <div class="card-header-actions">
      <h5 class="card-title">{{ titulo }}</h5>
      <button class="btn-download" @click="descargarGrafico" title="Descargar imagen">
        <i class="bi bi-download"></i>
      </button>
    </div>
    
    <div class="chart-container">
      <v-chart 
        ref="barChart" 
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
import { BarChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  ToolboxComponent // Necesario para algunas funciones internas
} from 'echarts/components';
import VChart from 'vue-echarts';

use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  ToolboxComponent
]);

export default {
  name: 'GraficoBarrasComparativas',
  components: {
    VChart,
  },
  props: {
    titulo: { type: String, default: 'Gráfico de Barras' },
    datosAnuales: {
      type: Object, 
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
    };
  },
  watch: {
    datosAnuales: { handler: 'crearChartOption', deep: true },
    isDark: 'crearChartOption',
  },
  mounted() {
    this.crearChartOption();
  },
  methods: {
    crearChartOption() {
      // 1. Extraer años dinámicamente
      const anos = Object.keys(this.datosAnuales).sort(); 
      
      if (anos.length === 0) {
        this.chartOption = {}; // Limpiar si no hay datos
        return;
      }

      const consumoData = anos.map(year => this.datosAnuales[year].consumo_total_kwh || 0);
      const costoData = anos.map(year => this.datosAnuales[year].costo_total || 0);

      // Colores según tema
      const textColor = this.isDark ? '#E0E0E0' : '#333333';
      const axisColor = this.isDark ? '#A0A0A0' : '#666666';
      const splitLineColor = this.isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
      
      // Colores de barras
      const colorConsumo = '#8A2BE2'; // Morado
      const colorCosto = '#00C853';   // Verde

      this.chartOption = {
        // Fondo transparente para la vista web, pero ECharts usará el del contenedor al exportar
        backgroundColor: 'transparent',
        
        color: [colorConsumo, colorCosto],
        
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: this.isDark ? 'rgba(40, 40, 60, 0.9)' : 'rgba(255, 255, 255, 0.9)',
          borderColor: this.isDark ? '#444' : '#DDD',
          textStyle: { color: textColor },
          formatter: (params) => {
            let tooltip = `<div style="margin-bottom: 5px; font-weight: bold">${params[0].name}</div>`;
            params.forEach(item => {
              let val = item.value.toLocaleString('es-MX', { maximumFractionDigits: 2 });
              let unit = item.seriesName.includes('Consumo') ? 'kWh' : 'MXN';
              tooltip += `
                <div style="display: flex; justify-content: space-between; gap: 15px; align-items: center">
                  <span>${item.marker} ${item.seriesName}</span>
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
          bottom: '10%', // Espacio para leyenda
          top: '15%',
          containLabel: true
        },
        
        xAxis: {
          type: 'category',
          data: anos,
          axisLine: { lineStyle: { color: axisColor } },
          axisLabel: { color: textColor, fontWeight: 'bold' }
        },
        
        yAxis: [
          {
            type: 'value',
            name: 'Consumo',
            position: 'left',
            axisLine: { show: true, lineStyle: { color: colorConsumo } },
            axisLabel: { formatter: '{value} k', color: colorConsumo },
            splitLine: { lineStyle: { type: 'dashed', color: splitLineColor } }
          },
          {
            type: 'value',
            name: 'Costo',
            position: 'right',
            axisLine: { show: true, lineStyle: { color: colorCosto } },
            axisLabel: { formatter: '${value} k', color: colorCosto },
            splitLine: { show: false }
          }
        ],
        
        series: [
          {
            name: 'Consumo (kWh)',
            type: 'bar',
            data: consumoData,
            yAxisIndex: 0,
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            barMaxWidth: 50 // Evita barras gigantes si hay pocos años
          },
          {
            name: 'Costo (MXN)',
            type: 'bar',
            data: costoData,
            yAxisIndex: 1,
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            barMaxWidth: 50
          }
        ]
      };
    },

    descargarGrafico() {
      const chartInstance = this.$refs.barChart;
      if (!chartInstance) return;

      // Obtener imagen en Base64
      const url = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2, // Alta resolución
        backgroundColor: this.isDark ? '#2B2B40' : '#FFFFFF' // Fondo según tema
      });

      // Crear enlace temporal para descarga
      const link = document.createElement('a');
      link.href = url;
      link.download = `Comparativa_Anual_${new Date().toISOString().slice(0,10)}.png`;
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
  position: relative;
}

.card-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;

  .card-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: inherit; // Hereda del tema
  }

  .btn-download {
    background: transparent;
    border: none;
    color: #99A2AD; // Gris suave
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;

    &:hover {
      color: #8A2BE2; // Morado
      background-color: rgba(138, 43, 226, 0.1);
    }
  }
}

.chart-container {
  flex-grow: 1;
  min-height: 0; // Fix para flexbox overflow
  position: relative;
}
</style>