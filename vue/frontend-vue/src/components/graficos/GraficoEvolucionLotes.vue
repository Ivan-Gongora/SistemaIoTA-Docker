<template>
  <div class="chart-card" :class="{ 'theme-dark': isDark }">
    <div class="card-header-actions">
      <div class="titles">
        <h5 class="card-title">{{ titulo }}</h5>
        <span class="metric-badge" v-if="metricaSeleccionada">
          <i class="bi bi-activity"></i> {{ getMetricaTitulo(metricaSeleccionada) }}
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
import { LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent, // 🟢 Importante para el desplazamiento
  MarkPointComponent,
  ToolboxComponent
} from 'echarts/components';
import * as echarts from 'echarts/core';
import VChart from 'vue-echarts';

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent, // 🟢 Registrar el componente
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

    hexToRgba(hex, alpha) {
        let r = 0, g = 0, b = 0;
        if (hex.length === 4) {
            r = parseInt("0x" + hex[1] + hex[1]);
            g = parseInt("0x" + hex[2] + hex[2]);
            b = parseInt("0x" + hex[3] + hex[3]);
        } else if (hex.length === 7) {
            r = parseInt("0x" + hex[1] + hex[2]);
            g = parseInt("0x" + hex[3] + hex[4]);
            b = parseInt("0x" + hex[5] + hex[6]);
        }
        return `rgba(${r},${g},${b},${alpha})`;
    },

    crearChartOption() {
      const { labels, series } = this.datosEvolucion;

      if (!labels || labels.length === 0 || !series || series.length === 0) {
        this.chartOption = {
          title: {
            text: 'Sin datos disponibles',
            left: 'center',
            top: 'center',
            textStyle: { color: this.isDark ? '#AAA' : '#999' }
          }
        };
        return;
      }

      const unit = this.getMetricaUnidad(this.metricaSeleccionada);
      const metricTitle = this.getMetricaTitulo(this.metricaSeleccionada);
      const textColor = this.isDark ? '#E4E6EB' : '#333333';
      const axisColor = this.isDark ? '#A0A0A0' : '#666666';
      const splitLineColor = this.isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

      const colores = [
        '#8A2BE2', '#00E676', '#FFD600', '#2979FF', 
        '#FF1744', '#AA00FF', '#00B0FF', '#F50057'
      ];

      this.chartOption = {
        backgroundColor: 'transparent',
        color: colores,

        tooltip: {
          trigger: 'axis',
          backgroundColor: this.isDark ? 'rgba(30, 30, 40, 0.95)' : 'rgba(255, 255, 255, 0.95)',
          borderColor: this.isDark ? '#444' : '#DDD',
          textStyle: { color: textColor },
          formatter: (params) => {
            let tooltip = `<div style="font-weight:bold; margin-bottom:5px; border-bottom:1px solid ${axisColor}">${params[0].name}</div>`;
            params.forEach(item => {
              if (item.value !== null && item.value !== undefined) {
                let val = Number(item.value).toLocaleString('es-MX', { maximumFractionDigits: 2 });
                tooltip += `<div style="display:flex; justify-content:space-between; gap:15px">
                  <span>${item.marker} ${item.seriesName}</span>
                  <span style="font-weight:bold">${val}${unit}</span>
                </div>`;
              }
            });
            return tooltip;
          }
        },

        legend: {
          data: series.map(s => s.name),
          top: 0,
          type: 'scroll',
          icon: 'roundRect',
          textStyle: { color: textColor }
        },

        grid: {
          left: '2%', right: '4%', bottom: '15%', top: '15%', containLabel: true
        },

        xAxis: {
          type: 'category',
          boundaryGap: false,
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

        // 🟢 DATAZOOM AGREGADO AQUÍ
        dataZoom: [
          {
            type: 'slider', // Barra inferior visible
            show: true,
            xAxisIndex: [0],
            start: 0, // Porcentaje inicial (0 = principio)
            end: 100, // Porcentaje final (100 = todo el rango)
            bottom: 5,
            height: 20,
            borderColor: 'transparent',
            handleStyle: { color: '#8A2BE2' },
            textStyle: { color: axisColor }
          },
          {
            type: 'inside', // Zoom con rueda del mouse
            xAxisIndex: [0],
            start: 0,
            end: 100
          }
        ],

        series: series.map((s, index) => {
            const colorBase = colores[index % colores.length];
            const dataLimpia = s.data.map(v => (v === 0 || v === '0') ? null : v);

            return {
                name: s.name,
                type: 'line',
                data: dataLimpia,
                connectNulls: true, // Conectar puntos lejanos
                smooth: 0.4, 
                symbol: 'circle',
                symbolSize: 6,
                showSymbol: false, 
                lineStyle: { width: 3, shadowColor: 'rgba(0,0,0,0.3)', shadowBlur: 5 },
                areaStyle: {
                    opacity: 0.3,
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: this.hexToRgba(colorBase, 0.5) },
                        { offset: 1, color: this.hexToRgba(colorBase, 0.0) }
                    ])
                },
                markPoint: {
                    data: [ { type: 'max', name: 'Máx', label: { color: '#fff', fontSize: 10 } } ],
                    itemStyle: { color: colorBase }
                },
                emphasis: {
                    focus: 'series',
                    scale: true
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
      link.download = `Evolucion_Lotes_${new Date().toISOString().slice(0,10)}.png`;
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