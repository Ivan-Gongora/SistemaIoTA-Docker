<template>
  <div class="chart-card" :class="{ 'theme-dark': isDark }">
    <div class="card-header-actions">
      <div class="titles">
        <h5 class="card-title">{{ titulo }}</h5>
        <span class="metric-badge" v-if="metricaSeleccionada">
          <i class="bi bi-bar-chart-fill"></i> {{ getMetricaTitulo(metricaSeleccionada) }}
        </span>
      </div>
      <button class="btn-download" @click="descargarGrafico" title="Descargar imagen HD">
        <i class="bi bi-camera"></i>
      </button>
    </div>
    
    <div class="chart-container">
      <v-chart 
        ref="evolutionChart" 
        class="chart" 
        :option="chartOption" 
        autoresize 
        :style="{ height: '100%', minHeight: '450px' }"
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
  DataZoomComponent,
  MarkPointComponent,
  ToolboxComponent
} from 'echarts/components';
import VChart from 'vue-echarts';

use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent,
  MarkPointComponent,
  ToolboxComponent
]);

export default {
  name: 'GraficoEvolucionSeries',
  components: { VChart },
  props: {
    titulo: { type: String, default: 'Evolución Histórica' },
    datosEvolucion: { type: Object, required: true },
    metricaSeleccionada: { type: String, default: 'consumo_total_kwh' },
    isDark: { type: Boolean, default: false },
  },
  data() {
    return {
      chartOption: {},
    };
  },
  watch: {
    datosEvolucion: { handler: 'crearChartOption', deep: true },
    metricaSeleccionada: 'crearChartOption',
    isDark: 'crearChartOption',
  },
  mounted() {
    this.crearChartOption();
  },
  methods: {
    getMetricaTitulo(key) {
      const titles = {
        'consumo_total_kwh': 'Consumo Eléctrico',
        'costo_total': 'Costo Total',
        'demanda_maxima_kw': 'Demanda Máxima',
        'factor_potencia': 'Factor de Potencia',
      };
      return titles[key] || 'Valor';
    },
    getMetricaUnidad(key) {
      const units = {
        'consumo_total_kwh': ' kWh',
        'costo_total': ' MXN',
        'demanda_maxima_kw': ' kW',
        'factor_potencia': '%',
      };
      return units[key] || '';
    },

    crearChartOption() {
      const { labels, series } = this.datosEvolucion;

      if (!labels || labels.length === 0 || !series || series.length === 0) {
        this.chartOption = {
          title: {
            text: 'Sin datos disponibles para visualizar',
            left: 'center',
            top: 'center',
            textStyle: { color: this.isDark ? '#AAA' : '#999', fontSize: 14 }
          }
        };
        return;
      }

      const unit = this.getMetricaUnidad(this.metricaSeleccionada);
      const metricTitle = this.getMetricaTitulo(this.metricaSeleccionada);
      const textColor = this.isDark ? '#E4E6EB' : '#333333';
      const axisColor = this.isDark ? '#A0A0A0' : '#666666';
      const splitLineColor = this.isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

      // 🟢 1. Definimos una paleta de colores vibrantes
      const colores = [
        '#8A2BE2', '#00E676', '#FFD600', '#2979FF', 
        '#FF1744', '#AA00FF', '#00B0FF', '#F50057',
        '#00BCD4', '#FF9800'
      ];

      this.chartOption = {
        backgroundColor: 'transparent',
        
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: this.isDark ? 'rgba(30, 30, 40, 0.95)' : 'rgba(255, 255, 255, 0.95)',
          borderColor: this.isDark ? '#444' : '#DDD',
          textStyle: { color: textColor },
          formatter: (params) => {
            // params[0] es el primer (y único) punto de dato en esa posición X
            const p = params[0];
            const name = p.name; // Ej: "2022-01"
            const val = Number(p.value).toLocaleString('es-MX', { maximumFractionDigits: 2 });
            // El color del punto viene dinámico
            const colorDot = `<span style="display:inline-block;margin-right:5px;width:10px;height:10px;background-color:${p.color};border-radius:2px;"></span>`;
            
            return `
              <div style="font-weight:bold; margin-bottom:5px; border-bottom:1px solid ${axisColor}; padding-bottom:3px;">${name}</div>
              <div style="display:flex; justify-content:space-between; gap:15px; align-items:center;">
                 <span>${colorDot} ${p.seriesName}</span>
                 <span style="font-weight:bold">${val}${unit}</span>
              </div>
            `;
          }
        },

        legend: {
          show: false, // Ocultamos leyenda estándar porque los colores varían por barra, no por serie
        },

        grid: {
          left: '2%', right: '4%', bottom: '10%', top: '15%', containLabel: true
        },

        xAxis: {
          type: 'category',
          data: labels,
          axisLabel: { color: textColor, fontWeight: 'bold' },
          axisLine: { lineStyle: { color: axisColor } }
        },

        yAxis: {
          type: 'value',
          name: metricTitle,
          nameTextStyle: { color: axisColor, padding: [0, 0, 0, 20] },
          axisLabel: { formatter: `{value}`, color: axisColor },
          axisLine: { show: false },
          splitLine: { lineStyle: { type: 'dashed', color: splitLineColor } }
        },

        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          { 
            type: 'slider', 
            show: true, 
            bottom: 5, 
            height: 15, 
            borderColor: 'transparent', 
            handleStyle: { color: '#8A2BE2' },
            textStyle: { color: axisColor } 
          }
        ],

        series: series.map((s) => {
            const dataLimpia = s.data.map(v => (v === 0 || v === '0') ? null : v);

            return {
                name: s.name,
                type: 'bar',
                data: dataLimpia,
                barMaxWidth: 60,
                
                // 🟢 2. Lógica de Colores Dinámicos
                itemStyle: {
                    borderRadius: [4, 4, 0, 0],
                    // Función que asigna color basado en el AÑO del label
                    color: (params) => {
                        // params.name es "2022-01", "2025-05", etc.
                        if (!params.name) return colores[0];
                        
                        // Extraemos el año (primeros 4 caracteres)
                        const year = params.name.substring(0, 4);
                        
                        // Convertimos el año a número para obtener un índice
                        const yearNum = parseInt(year);
                        
                        // Usamos módulo para ciclar colores si hay muchos años
                        // Esto garantiza que todo "2022" sea de un color y todo "2025" de otro
                        if (!isNaN(yearNum)) {
                           // Truco para asignar índices fijos: 
                           // 2022 -> index X, 2025 -> index Y
                           return colores[yearNum % colores.length];
                        }
                        return colores[0];
                    }
                },

                markPoint: {
                    data: [
                        { type: 'max', name: 'Máx', label: { color: '#fff', fontSize: 10, offset: [0, -2] } }
                    ],
                    symbolSize: 35,
                    symbolOffset: [0, -15]
                },

                emphasis: {
                    focus: 'series',
                    itemStyle: {
                        // Al hacer hover, oscurecemos ligeramente
                        shadowBlur: 10,
                        shadowColor: 'rgba(0,0,0,0.3)'
                    }
                }
            };
        })
      };
    },

    descargarGrafico() {
      const chartInstance = this.$refs.evolutionChart;
      if (!chartInstance) return;

      const bgColor = this.isDark ? '#2B2B40' : '#FFFFFF';
      const url = chartInstance.getDataURL({
        type: 'png', pixelRatio: 2, backgroundColor: bgColor
      });
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `Evolucion_Barras_Lotes_${new Date().toISOString().slice(0,10)}.png`;
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
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(150, 150, 150, 0.1);

  .titles {
    display: flex;
    flex-direction: column;
    gap: 5px;

    .card-title {
      margin: 0;
      font-size: 1.1rem;
      font-weight: 700;
      color: inherit;
    }

    .metric-badge {
      font-size: 0.75rem;
      color: #99A2AD;
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      i { color: #8A2BE2; }
    }
  }

  .btn-download {
    background: transparent;
    border: 1px solid rgba(150, 150, 150, 0.2);
    color: #99A2AD;
    cursor: pointer;
    width: 34px;
    height: 34px;
    border-radius: 8px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      color: #8A2BE2;
      border-color: #8A2BE2;
      background-color: rgba(138, 43, 226, 0.05);
      transform: translateY(-2px);
    }
    i { font-size: 1rem; }
  }
}

.chart-container {
  flex-grow: 1;
  min-height: 0;
  position: relative;
}
</style>