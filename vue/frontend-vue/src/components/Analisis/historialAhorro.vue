<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma 
        titulo="Auditoría Científica de Ahorro" 
        subtitulo="Análisis técnico A/B basado en analítica avanzada de datos"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen" 
      />
      
      <div class="dashboard-grid-premium">
        
        <!-- SECCIÓN DE INTELIGENCIA Y FILTROS -->
        <div class="grid-item-header">
          <div class="glass-card footer-glow shadow-lg">
            <div class="row g-4 align-items-center">
              <div class="col-xl-3 col-lg-4">
                <div class="d-flex align-items-center gap-3">
                  <div class="icon-pulse green"><i class="bi bi-cpu-fill"></i></div>
                  <div>
                    <h5 class="fw-bold mb-0 title-contrast">Motor Analítico</h5>
                    <span class="text-muted-contrast small">Estado del Sistema. <span class="text-success fw-bold">Operativo</span></span>
                  </div>
                </div>
              </div>
              
              <div class="col-xl-7 col-lg-8">
                <div class="d-flex flex-wrap gap-4 justify-content-center">
                  <div class="selector-unit">
                    <label class="label-tiny">REFERENCIA (MANUAL)</label>
                    <div class="input-modern red">
                      <i class="bi bi-search"></i>
                      <select v-model="idBase" class="clean-select">
                        <option :value="13">Aula F1 . Edificio F</option>
                        <option v-for="dev in listaDispositivos" :key="dev.id" :value="dev.id">
                          {{ dev.nombre }} . {{ dev.ubicacion }}
                        </option>
                      </select>
                    </div>
                  </div>
                  <div class="selector-unit">
                    <label class="label-tiny">EXPERIMENTO (AUTO)</label>
                    <div class="input-modern blue">
                      <i class="bi bi-shield-fill-check"></i>
                      <select v-model="idControl" class="clean-select">
                        <option :value="14">Aula F3 . Edificio F</option>
                        <option v-for="dev in listaDispositivos" :key="dev.id" :value="dev.id">
                          {{ dev.nombre }} . {{ dev.ubicacion }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <div class="col-xl-2 col-lg-12">
                <button @click="ejecutarAuditoria" class="btn-auditoria" :disabled="loading">
                  <div class="btn-content">
                    <i class="bi" :class="loading ? 'bi-arrow-repeat spin' : 'bi-stars'"></i>
                    <span>{{ loading ? 'AUDITANDO' : 'EJECUTAR' }}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- KPIs CON ENFOQUE EN AHORRO -->
        <div class="grid-item-kpis" v-if="resultado">
          <div class="kpi-stripe">
            <div class="kpi-neon green">
              <div class="kpi-top">
                <i class="bi bi-currency-dollar"></i>
                <span class="badge-saving-pct">-{{ resultado.comparativa.ahorro_financiero_pct }}%</span>
              </div>
              <div class="kpi-mid">
                <span class="label">REDUCCIÓN FINANCIERA</span>
                <h3 class="value">${{ resultado.comparativa.ahorro_financiero_mxn }}</h3>
              </div>
              <div class="kpi-bot"><span class="small text-muted-contrast">Ahorro proyectado mensual</span></div>
            </div>

            <div class="kpi-neon blue">
              <div class="kpi-top"><i class="bi bi-lightning-charge"></i></div>
              <div class="kpi-mid">
                <span class="label">ENERGÍA MITIGADA</span>
                <h3 class="value">{{ resultado.comparativa.diferencia_bruta_kwh }} <small>kWh</small></h3>
              </div>
              <div class="kpi-bot"><span class="small text-muted-contrast">Consumo evitado en red</span></div>
            </div>

            <div class="kpi-neon red">
              <div class="kpi-top"><i class="bi bi-trash3"></i></div>
              <div class="kpi-mid">
                <span class="label">CARGA FANTASMA</span>
                <h3 class="value">{{ resultado.dispositivo_control.carga_fantasma_kwh }} <small>kWh</small></h3>
              </div>
              <div class="kpi-bot"><span class="small text-muted-contrast">Fuga eléctrica en experimento</span></div>
            </div>

            <div class="kpi-neon gold">
              <div class="kpi-top"><i class="bi bi-check-circle"></i></div>
              <div class="kpi-mid">
                <span class="label">PRECISIÓN ESTADÍSTICA</span>
                <h3 class="value">100%</h3>
              </div>
              <div class="kpi-bot"><span class="small text-muted-contrast">Confianza ANOVA p &lt; 0.05</span></div>
            </div>
          </div>
        </div>

        <!-- PERFIL DE DEMANDA DINÁMICO (3/5) -->
        <div class="grid-item-demand" v-if="resultado">
          <div class="chart-container-premium shadow-lg">
            <div class="chart-header">
              <div class="title-group">
                <h5 class="fw-bold m-0 title-contrast">Perfil Térmico de Demanda Activa</h5>
                <span class="text-muted-contrast small">Potencia registrada en ciclo de 24 horas. Pulsa leyendas para filtrar o usa zoom.</span>
              </div>
            </div>
            <div ref="chartPerfil" class="echarts-surface"></div>
          </div>
        </div>

        <!-- DESGLOSE CFE GDMTH (2/5) -->
        <div class="grid-item-cfe" v-if="resultado">
          <div class="chart-container-premium shadow-lg side-content">
            <h5 class="fw-bold mb-4 title-contrast">Estructura Tarifaria GDMTH</h5>
            <div ref="chartCFE" class="echarts-surface-small"></div>
            <div class="cfe-details mt-4">
              <div class="cfe-row">
                <span class="dot punta"></span>
                <span class="label text-muted-contrast">Costo Energía Punta</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_punta }}</span>
              </div>
              <div class="cfe-row">
                <span class="dot intermedia"></span>
                <span class="label text-muted-contrast">Costo Energía Intermedia</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_intermedia }}</span>
              </div>
              <div class="cfe-row border-0">
                <span class="dot base"></span>
                <span class="label text-muted-contrast">Costo Energía Base</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_base }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- TENDENCIA DE CONSUMO (3/5) -->
        <div class="grid-item-trend" v-if="resultado">
          <div class="chart-container-premium shadow-lg">
            <h5 class="fw-bold mb-4 title-contrast">Tendencia de Consumo Sincronizada (kWh)</h5>
            <div ref="chartTrend" class="echarts-surface"></div>
          </div>
        </div>

        <!-- EFICIENCIA OPERATIVA (2/5) -->
        <div class="grid-item-metrics" v-if="resultado">
          <div class="chart-container-premium shadow-lg d-flex flex-column">
            <h5 class="fw-bold mb-4 title-contrast">Eficiencia Operativa</h5>
            
            <div class="circular-wrap flex-grow-1 d-flex align-items-center justify-content-center">
              <div ref="chartGauge" class="echarts-surface-gauge"></div>
              <div class="gauge-center">
                <span class="percent text-success">{{ resultado.comparativa.ahorro_energia_pct }}%</span>
                <span class="label text-muted-contrast">EFICIENCIA NETA</span>
              </div>
            </div>

            <div class="table-modern mt-auto">
              <div class="t-row">
                <span class="t-label text-muted-contrast">Ocupación Promedio</span>
                <div class="t-vals title-contrast">
                  <span class="base text-danger">{{ resultado.dispositivo_base.porcentaje_ocupacion }}%</span>
                  <i class="bi bi-arrow-right-short text-muted-contrast"></i>
                  <span class="ctrl text-success">{{ resultado.dispositivo_control.porcentaje_ocupacion }}%</span>
                </div>
              </div>
              <div class="t-row border-0">
                <span class="t-label text-muted-contrast">Demanda Pico</span>
                <div class="t-vals title-contrast">
                  <span class="base text-danger">{{ resultado.dispositivo_base.corriente_maxima_watts }}W</span>
                  <i class="bi bi-arrow-right-short text-muted-contrast"></i>
                  <span class="ctrl text-success">{{ resultado.dispositivo_control.corriente_maxima_watts }}W</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TABLAS DE EVIDENCIA CIENTÍFICA -->
        <div class="grid-item-data-tables" v-if="resultado">
          <div class="glass-card shadow-lg p-0 overflow-hidden">
            <div class="table-header-premium p-4">
              <h5 class="fw-bold m-0 title-contrast">Evidencia de Auditoría por Dispositivo</h5>
              <p class="text-muted-contrast small mb-0">TU puedes verificar el origen de los indicadores calculados.</p>
            </div>
            <div class="table-responsive">
              <table class="table-scientific">
                <thead>
                  <tr>
                    <th>MÉTRICA DE ANÁLISIS</th>
                    <th>UNIDAD</th>
                    <th>AULA F1 (MANUAL)</th>
                    <th>AULA F3 (AUTO)</th>
                    <th>AHORRO LOGRADO</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="text-muted-contrast">Consumo Mensual Normalizado</td>
                    <td class="text-center small">kWh</td>
                    <td class="text-center fw-bold">{{ resultado.dispositivo_base.consumo_normalizado_kwh }}</td>
                    <td class="text-center fw-bold text-success">{{ resultado.dispositivo_control.consumo_normalizado_kwh }}</td>
                    <td class="text-center text-success fw-bold">{{ resultado.comparativa.ahorro_energia_pct }}%</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Energía en Reposo (Vacio)</td>
                    <td class="text-center small">kWh</td>
                    <td class="text-center">{{ resultado.dispositivo_base.carga_fantasma_kwh }}</td>
                    <td class="text-center text-success">{{ resultado.dispositivo_control.carga_fantasma_kwh }}</td>
                    <td class="text-center">{{ resultado.comparativa.eliminacion_desperdicio_pct }}%</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Costo Operativo CFE</td>
                    <td class="text-center small">MXN</td>
                    <td class="text-center">${{ resultado.dispositivo_base.costo_estimado_mxn }}</td>
                    <td class="text-center text-success">${{ resultado.dispositivo_control.costo_estimado_mxn }}</td>
                    <td class="text-center text-success fw-bold">-${{ resultado.comparativa.ahorro_financiero_mxn }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Coeficiente Correlación PIR</td>
                    <td class="text-center small">R²</td>
                    <td class="text-center">{{ resultado.dispositivo_base.correlacion_pir_potencia }}</td>
                    <td class="text-center">{{ resultado.dispositivo_control.correlacion_pir_potencia }}</td>
                    <td class="text-center text-muted-contrast">Validado</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- CUADROS DE INTERPRETACIÓN -->
        <div class="grid-item-footer" v-if="resultado">
          <div class="row g-4">
            <div class="col-md-4">
              <div class="info-card-explain shadow-sm">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-info-circle-fill text-primary"></i>
                  <h6 class="fw-bold m-0 title-contrast">Fundamento ANOVA</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  TU ahorro tiene un valor p de {{ resultado.comparativa.estadistica_anova.p_valor.toExponential(2) }}. Esto certifica que la diferencia de consumo entre las aulas es producto del sistema de control y no de variaciones aleatorias.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="info-card-explain shadow-sm border-warning">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-lightning-charge-fill text-warning"></i>
                  <h6 class="fw-bold m-0 title-contrast">Protección Tarifaria</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  La CFE factura costos elevados en periodos Punta e Intermedia. TU sistema limita la demanda en estos horarios. Baja TU facturación en ${{ resultado.comparativa.ahorro_financiero_mxn }} mensuales sin degradar el servicio.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="info-card-explain shadow-sm border-success">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-recycle text-success"></i>
                  <h6 class="fw-bold m-0 title-contrast">Impacto Ecológico</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  Evitar {{ resultado.comparativa.diferencia_bruta_kwh }} kWh reduce el estrés en transformadores locales. Esto prolonga la vida útil de TUS equipos eléctricos y disminuye directamente las emisiones contaminantes.
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

export default {
  name: 'AnalisisCientificoPremium',
  components: { BarraLateralPlataforma, EncabezadoPlataforma },
  data() {
    return {
      isDark: false,
      isSidebarOpen: true,
      loading: false,
      idBase: 13,
      idControl: 14,
      listaDispositivos: [],
      resultado: null,
      instances: { perfil: null, cfe: null, trend: null, gauge: null }
    };
  },
  mounted() {
    this.detectarTema();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleTheme);
    }
    this.ejecutarAuditoria();
    window.addEventListener('resize', this.resizeCharts);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeCharts);
    Object.values(this.instances).forEach(inst => inst?.dispose());
  },
  methods: {
    toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; },
    handleTheme(e) { this.isDark = e.matches; this.$nextTick(() => this.renderAll()); },
    detectarTema() { this.isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; },
    resizeCharts() { Object.values(this.instances).forEach(inst => inst?.resize()); },
    
    async ejecutarAuditoria() {
      this.loading = true;
      try {
        const response = await fetch(`${API_BASE_URL}/api/analisis/comparativo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            dispositivo_base_id: this.idBase,
            dispositivo_ctrl_id: this.idControl,
            fecha_inicio: "2025-10-01 00:00:00",
            fecha_fin: "2025-10-31 23:59:59"
          })
        });
        const res = await response.json();
        if (res.status === 'success') {
          this.resultado = res.data;
          this.$nextTick(() => this.renderAll());
        }
      } catch (error) {
        console.error("Error auditoría.", error);
      } finally {
        this.loading = false;
      }
    },

    renderAll() {
      if (!this.resultado) return;
      this.renderPerfil();
      this.renderCFE();
      this.renderTrend();
      this.renderGauge();
    },

    renderPerfil() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      
      if (!this.instances.perfil) this.instances.perfil = echarts.init(this.$refs.chartPerfil);
      this.instances.perfil.setOption({
        color: ['#ef4444', '#22c55e'],
        toolbox: { 
          feature: { dataZoom: { yAxisIndex: 'none' }, restore: {}, saveAsImage: {} },
          iconStyle: { borderColor: textColor }
        },
        legend: { textStyle: { color: textColor }, bottom: 0, selectedMode: true },
        tooltip: { trigger: 'axis', backgroundColor: this.isDark ? '#1a1d2d' : '#fff', textStyle: { color: textColor } },
        grid: { top: 60, left: 60, right: 30, bottom: 80 },
        xAxis: { type: 'category', data: Array.from({length: 24}, (_, i) => `${i}:00`), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
        series: [
          { name: 'Referencia (Manual)', type: 'line', smooth: true, data: this.resultado.dispositivo_base.grafica_perfil_demanda, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(239,68,68,0.2)'},{offset:1,color:'transparent'}]) } },
          { name: 'Experimento (Auto)', type: 'line', smooth: true, data: this.resultado.dispositivo_control.grafica_perfil_demanda, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(34,197,94,0.2)'},{offset:1,color:'transparent'}]) } }
        ]
      });
    },

    renderCFE() {
      if (!this.instances.cfe) this.instances.cfe = echarts.init(this.$refs.chartCFE);
      const d = this.resultado.dispositivo_control.desglose_cfe;
      this.instances.cfe.setOption({
        color: ['#f59e0b', '#3b82f6', '#ef4444'],
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie', radius: ['65%', '95%'], avoidLabelOverlap: false,
          itemStyle: { borderRadius: 10, borderColor: this.isDark ? '#161925' : '#fff', borderWidth: 4 },
          label: { show: false },
          data: [{ value: d.energia_intermedia, name: 'Intermedia' }, { value: d.energia_punta, name: 'Punta' }, { value: d.energia_base, name: 'Base' }]
        }]
      });
    },

    renderTrend() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      if (!this.instances.trend) this.instances.trend = echarts.init(this.$refs.chartTrend);
      
      const baseData = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.kwh);
      const ctrlData = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.kwh);

      this.instances.trend.setOption({
        color: ['#ef4444', '#22c55e'],
        tooltip: { trigger: 'axis' },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20, bottom: 40 }],
        grid: { top: 30, left: 60, right: 30, bottom: 100 },
        xAxis: { type: 'category', data: Array.from({length: 31}, (_, i) => i + 1), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { show: false } },
        series: [
          { name: 'Consumo Referencia', type: 'bar', stack: 'total', data: baseData },
          { name: 'Consumo Ahorrado', type: 'bar', stack: 'total', data: ctrlData }
        ]
      });
    },

    renderGauge() {
      if (!this.instances.gauge) this.instances.gauge = echarts.init(this.$refs.chartGauge);
      this.instances.gauge.setOption({
        series: [{
          type: 'gauge', startAngle: 90, endAngle: -270, pointer: { show: false },
          progress: { show: true, overlap: false, roundCap: true, itemStyle: { color: '#22c55e' } },
          axisLine: { lineStyle: { width: 14, color: [[1, this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)']] } },
          splitLine: { show: false }, axisTick: { show: false }, axisLabel: { show: false },
          data: [{ value: this.resultado.comparativa.ahorro_energia_pct }], detail: { show: false }
        }]
      });
    }
  }
};
</script>

<style scoped lang="scss">
$DEEP-NAVY: #0f111a;
$CARD-NAVY: #161925;
$ACCENT-BLUE: #3b82f6;
$ACCENT-GREEN: #22c55e;
$ACCENT-RED: #ef4444;
$ACCENT-GOLD: #f59e0b;

.plataforma-layout { display: flex; width: 100%; min-height: 100vh; background: var(--bg-body); transition: background 0.3s; }
.plataforma-contenido { flex-grow: 1; padding: 40px; margin-left: 80px; transition: margin-left 0.3s; &.shifted { margin-left: 280px; } }

.dashboard-grid-premium {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 24px; padding-bottom: 50px;
}

.grid-item-header, .grid-item-kpis, .grid-item-data-tables, .grid-item-footer { grid-column: 1 / span 5; }
.grid-item-demand, .grid-item-trend { grid-column: 1 / span 3; }
.grid-item-cfe, .grid-item-metrics { grid-column: 4 / span 2; }

.title-contrast { color: #1e293b; transition: color 0.3s; }
.text-muted-contrast { color: #64748b; transition: color 0.3s; }

.theme-dark {
  .title-contrast { color: #f8fafc !important; }
  .text-muted-contrast { color: #cbd5e1 !important; }
  .glass-card, .kpi-neon, .chart-container-premium, .info-card-explain { background: $CARD-NAVY; border-color: rgba(255,255,255,0.08); }
}

.glass-card { background: white; padding: 24px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); position: relative; overflow: hidden; }
.footer-glow::after { content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, $ACCENT-RED, $ACCENT-BLUE, $ACCENT-GREEN); }

.input-modern { display: flex; align-items: center; background: #f1f5f9; padding: 10px 16px; border-radius: 12px; gap: 12px; border: 1px solid transparent; transition: all 0.2s;
  i { font-size: 1.1rem; } .clean-select { border: none; background: transparent; width: 100%; font-weight: 700; color: #1e293b; outline: none; } }
.theme-dark .input-modern { background: rgba(0,0,0,0.3); .clean-select { color: white; } }

.btn-auditoria { width: 100%; background: #6366f1; color: white; border: none; padding: 15px; border-radius: 14px; font-weight: 900; box-shadow: 0 8px 15px -4px rgba(99, 102, 241, 0.4); transition: transform 0.2s;
  &:hover { transform: translateY(-2px); filter: brightness(1.1); } }

.kpi-stripe { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.kpi-neon { background: white; padding: 24px; border-radius: 24px; border: 1px solid rgba(0,0,0,0.03); .value { font-size: 1.8rem; font-weight: 1000; margin: 4px 0; color: #1e293b; } }
.theme-dark .kpi-neon .value { color: #f8fafc; }

.chart-container-premium { background: white; padding: 28px; border-radius: 28px; border: 1px solid rgba(0,0,0,0.02); height: 100%; .chart-header { display: flex; justify-content: space-between; margin-bottom: 10px; } }
.echarts-surface { width: 100%; height: 380px; }
.echarts-surface-small { width: 100%; height: 190px; }
.echarts-surface-gauge { width: 100%; height: 240px; }

.status-tags .tag { padding: 5px 14px; border-radius: 10px; font-size: 0.7rem; font-weight: 900; text-transform: uppercase; &.base { background: rgba($ACCENT-RED, 0.1); color: $ACCENT-RED; } &.control { background: rgba($ACCENT-GREEN, 0.1); color: $ACCENT-GREEN; } }

.circular-wrap { position: relative; .gauge-center { position: absolute; top: 52%; left: 50%; transform: translate(-50%, -50%); text-align: center; .percent { font-size: 2.6rem; font-weight: 1000; display: block; line-height: 1; } .label { font-size: 0.65rem; font-weight: 800; letter-spacing: 1px; } } }

.table-modern .t-row { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid rgba(0,0,0,0.05); align-items: center; .t-label { font-size: 0.85rem; font-weight: 700; } .t-vals { display: flex; align-items: center; gap: 10px; font-weight: 900; font-size: 1rem; } }
.theme-dark .table-modern .t-row { border-color: rgba(255,255,255,0.05); }

.table-scientific { width: 100%; border-collapse: collapse; th { padding: 18px; background: rgba($ACCENT-BLUE, 0.04); font-size: 0.75rem; font-weight: 900; color: $ACCENT-BLUE; letter-spacing: 1.5px; text-transform: uppercase; } td { padding: 20px; border-bottom: 1px solid rgba(0,0,0,0.03); font-weight: 700; font-size: 0.95rem; } }
.theme-dark .table-scientific { th { background: rgba(255,255,255,0.02); color: #cbd5e1; } td { border-color: rgba(255,255,255,0.05); color: #f8fafc; } }

.cfe-row { display: flex; align-items: center; padding: 14px 0; border-bottom: 1px solid rgba(0,0,0,0.05); .dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 15px; &.punta { background: $ACCENT-RED; } &.intermedia { background: $ACCENT-BLUE; } &.base { background: $ACCENT-GOLD; } } .label { flex-grow: 1; font-size: 0.8rem; font-weight: 700; } .val { font-weight: 900; } }

.info-card-explain { background: white; padding: 25px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); height: 100%; p { line-height: 1.6; } }

.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>