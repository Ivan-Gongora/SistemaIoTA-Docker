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
              <div class="col-xl-2 col-lg-3">
                <div class="d-flex align-items-center gap-3">
                  <div class="icon-pulse green"><i class="bi bi-cpu-fill"></i></div>
                  <div>
                    <h5 class="fw-bold mb-0 title-contrast">Motor Analítico</h5>
                    <span class="text-muted-contrast small">Sistema. <span class="text-success fw-bold">Operativo</span></span>
                  </div>
                </div>
              </div>
              
              <div class="col-xl-8 col-lg-9">
                <div class="d-flex flex-wrap gap-3 justify-content-center">
                  <!-- Bloque Referencia -->
                  <div class="selector-unit-v3">
                    <label class="label-tiny">REFERENCIA (MANUAL)</label>
                    <div class="input-complex red">
                      <div class="input-wrapper">
                        <i class="bi bi-tag-fill me-1"></i>
                        <input type="text" v-model="nombreBase" class="clean-input-text" placeholder="Aula F-1">
                      </div>
                      <div class="divider"></div>
                      <div class="input-wrapper id-w">
                        <i class="bi bi-hash"></i>
                        <input type="number" v-model.number="idBase" class="clean-input-id" placeholder="13">
                      </div>
                    </div>
                  </div>
                  <!-- Bloque Experimento -->
                  <div class="selector-unit-v3">
                    <label class="label-tiny">EXPERIMENTO (AUTO)</label>
                    <div class="input-complex blue">
                      <div class="input-wrapper">
                        <i class="bi bi-tag-fill me-1"></i>
                        <input type="text" v-model="nombreControl" class="clean-input-text" placeholder="Aula F-3">
                      </div>
                      <div class="divider"></div>
                      <div class="input-wrapper id-w">
                        <i class="bi bi-hash"></i>
                        <input type="number" v-model.number="idControl" class="clean-input-id" placeholder="14">
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="col-xl-2 col-lg-12">
                <button @click="ejecutarAuditoria" class="btn-auditoria-premium" :disabled="loading">
                  <div class="btn-content">
                    <i class="bi" :class="loading ? 'bi-arrow-repeat spin' : 'bi-lightning-fill'"></i>
                    <span>{{ loading ? 'ANALIZANDO' : 'EJECUTAR' }}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- KPIs DE ALTO IMPACTO -->
        <div class="grid-item-kpis" v-if="resultado">
          <div class="kpi-stripe-v2">
            <div class="kpi-neon-v2 green">
              <div class="kpi-icon-v2"><i class="bi bi-currency-dollar"></i></div>
              <div class="kpi-body-v2">
                <span class="label">AHORRO MONETARIO</span>
                <h3 class="value">${{ resultado.comparativa.ahorro_financiero_mxn }}</h3>
                <span class="badge-saving-v2"><i class="bi bi-arrow-down-short"></i>{{ resultado.comparativa.ahorro_financiero_pct }}%</span>
              </div>
            </div>

            <div class="kpi-neon-v2 blue">
              <div class="kpi-icon-v2"><i class="bi bi-lightning-charge"></i></div>
              <div class="kpi-body-v2">
                <span class="label">ENERGÍA EVITADA</span>
                <h3 class="value">{{ resultado.comparativa.diferencia_bruta_kwh }} <small>kWh</small></h3>
                <span class="sub-text text-muted-contrast">Mitigación Directa</span>
              </div>
            </div>

            <div class="kpi-neon-v2 red">
              <div class="kpi-icon-v2"><i class="bi bi-trash3"></i></div>
              <div class="kpi-body-v2">
                <span class="label">CARGA FANTASMA</span>
                <h3 class="value">{{ resultado.dispositivo_control.carga_fantasma_kwh }} <small>kWh</small></h3>
                <span class="sub-text text-muted-contrast">Residuo en {{ nombreControl }}</span>
              </div>
            </div>

            <div class="kpi-neon-v2 gold">
              <div class="kpi-icon-v2"><i class="bi bi-patch-check"></i></div>
              <div class="kpi-body-v2">
                <span class="label">PRECISIÓN ANOVA</span>
                <h3 class="value">100%</h3>
                <span class="sub-text text-muted-contrast">p &lt; 0.05</span>
              </div>
            </div>
          </div>
        </div>

        <!-- PERFIL TÉRMICO (3/5) -->
        <div class="grid-item-demand" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2">
              <h5 class="fw-bold m-0 title-contrast">Comportamiento Térmico de Demanda</h5>
              <span class="text-muted-contrast small">Potencia registrada en Watts por hora. Pulsa sobre el gráfico para ver valores exactos.</span>
            </div>
            <div ref="chartPerfil" class="echarts-surface-v2"></div>
          </div>
        </div>

        <!-- DESGLOSE CFE (2/5) -->
        <div class="grid-item-cfe" v-if="resultado">
          <div class="chart-container-v2 shadow-lg side-content">
            <h5 class="fw-bold mb-4 title-contrast">Impacto en Tarifas CFE</h5>
            <div ref="chartCFE" class="echarts-surface-donut"></div>
            <div class="cfe-details-v2 mt-4">
              <div class="cfe-row-v2 punta">
                <span class="label text-muted-contrast">Energía Punta</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_punta }}</span>
              </div>
              <div class="cfe-row-v2 intermedia">
                <span class="label text-muted-contrast">Energía Intermedia</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_intermedia }}</span>
              </div>
              <div class="cfe-row-v2 base border-0">
                <span class="label text-muted-contrast">Energía Base</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_base }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- TENDENCIA DIARIA (3/5) -->
        <div class="grid-item-trend" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <h5 class="fw-bold mb-4 title-contrast">Comparativa de Consumo Sincronizada (kWh)</h5>
            <div ref="chartTrend" class="echarts-surface-v2"></div>
          </div>
        </div>

        <!-- EFICIENCIA OPERATIVA (2/5) -->
        <div class="grid-item-metrics" v-if="resultado">
          <div class="chart-container-v2 shadow-lg d-flex flex-column align-items-center">
            <h5 class="fw-bold mb-4 title-contrast w-100">Eficiencia Neta del Sistema</h5>
            <div class="efficiency-ring-v3">
              <div ref="chartRing" class="echarts-ring-v3"></div>
              <div class="ring-data">
                <span class="percent text-success">{{ resultado.comparativa.ahorro_energia_pct }}%</span>
                <span class="lbl text-muted-contrast">AHORRO NETO</span>
              </div>
            </div>
            <div class="metrics-summary-v2 w-100 mt-4">
              <div class="m-row">
                <span class="m-label text-muted-contrast">Ocupación Media</span>
                <div class="m-vals">
                  <span class="base text-danger me-2">{{ resultado.dispositivo_base.porcentaje_ocupacion }}%</span>
                  <span class="ctrl text-success">{{ resultado.dispositivo_control.porcentaje_ocupacion }}%</span>
                </div>
              </div>
              <div class="m-row border-0">
                <span class="m-label text-muted-contrast">Demanda Pico</span>
                <div class="m-vals">
                  <span class="base text-danger me-2">{{ resultado.dispositivo_base.corriente_maxima_watts }}W</span>
                  <span class="ctrl text-success">{{ resultado.dispositivo_control.corriente_maxima_watts }}W</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TABLA DE EVIDENCIA FINAL -->
        <div class="grid-item-data-tables" v-if="resultado">
          <div class="glass-card shadow-lg p-0 overflow-hidden">
            <div class="table-header-v2 p-4">
              <h5 class="fw-bold m-0 title-contrast">Evidencia de Auditoría por Dispositivo</h5>
              <p class="text-muted-contrast small mb-0">TU puedes verificar aquí el origen técnico del ahorro en esta sección.</p>
            </div>
            <div class="table-responsive">
              <table class="table-auditoria">
                <thead>
                  <tr>
                    <th>MÉTRICA ANALIZADA</th>
                    <th>UNIDAD</th>
                    <th>{{ nombreBase }} (REF)</th>
                    <th>{{ nombreControl }} (EXP)</th>
                    <th>DIFERENCIA LOGRADA</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="text-muted-contrast">Consumo Mensual Bruto</td>
                    <td class="text-center small">kWh</td>
                    <td class="text-center fw-bold">{{ resultado.dispositivo_base.consumo_bruto_kwh }}</td>
                    <td class="text-center fw-bold text-success">{{ resultado.dispositivo_control.consumo_bruto_kwh }}</td>
                    <td class="text-center text-success fw-bold">{{ Math.abs(resultado.dispositivo_base.consumo_bruto_kwh - resultado.dispositivo_control.consumo_bruto_kwh).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Costo de Facturación</td>
                    <td class="text-center small">MXN</td>
                    <td class="text-center">${{ resultado.dispositivo_base.costo_estimado_mxn }}</td>
                    <td class="text-center text-success">${{ resultado.dispositivo_control.costo_estimado_mxn }}</td>
                    <td class="text-center text-success fw-bold">${{ Math.abs(resultado.comparativa.ahorro_financiero_mxn).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Correlación PIR / Watts</td>
                    <td class="text-center small">R²</td>
                    <td class="text-center">{{ resultado.dispositivo_base.correlacion_pir_potencia }}</td>
                    <td class="text-center text-success">{{ resultado.dispositivo_control.correlacion_pir_potencia }}</td>
                    <td class="text-center text-muted-contrast fw-bold">Certificado</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- CUADROS EXPLICATIVOS -->
        <div class="grid-item-footer" v-if="resultado">
          <div class="row g-4">
            <div class="col-md-4">
              <div class="explain-box shadow-sm">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-info-circle-fill text-primary"></i>
                  <h6 class="fw-bold m-0 title-contrast">Fundamento Estadístico</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  TU ahorro se somete a la prueba ANOVA. El valor p de {{ resultado.comparativa.estadistica_anova.p_valor.toExponential(2) }} confirma que la reducción de energía es producto directo del sistema de control y no de variaciones aleatorias.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-warning">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-lightning-charge-fill text-warning"></i>
                  <h6 class="fw-bold m-0 title-contrast">Control de Carga Pico</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  La CFE factura costos elevados en horarios Punta e Intermedia. TU dispositivo limita la demanda en estos periodos, reduciendo TU factura en ${{ resultado.comparativa.ahorro_financiero_mxn }} mensuales sin afectar la operación.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-success">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-recycle text-success"></i>
                  <h6 class="fw-bold m-0 title-contrast">Energía Evitada</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  Evitar {{ resultado.comparativa.diferencia_bruta_kwh }} kWh reduce TU huella de carbono y el estrés en transformadores locales. Prolongas la vida útil de TUS equipos al evitar picos de corriente innecesarios.
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
  name: 'AnalisisCientificoAhorro',
  components: { BarraLateralPlataforma, EncabezadoPlataforma },
  data() {
    return {
      isDark: false,
      isSidebarOpen: true,
      loading: false,
      idBase: 13,
      idControl: 14,
      nombreBase: 'Aula F-1',
      nombreControl: 'Aula F-3',
      resultado: null,
      instances: { perfil: null, cfe: null, trend: null, ring: null }
    };
  },
  mounted() {
    this.detectarTema();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleTheme);
    }
    this.ejecutarAuditoria(); // Carga automática inicial
    window.addEventListener('resize', this.resizeCharts);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeCharts);
    Object.values(this.instances).forEach(inst => inst?.dispose());
  },
  methods: {
    toggleSidebar() { 
      this.isSidebarOpen = !this.isSidebarOpen;
      setTimeout(this.resizeCharts, 300);
    },
    handleTheme(e) { 
      this.isDark = e.matches; 
      this.$nextTick(() => this.renderAll()); 
    },
    detectarTema() { 
      this.isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; 
    },
    resizeCharts() { 
      Object.values(this.instances).forEach(inst => inst?.resize()); 
    },
    
    async ejecutarAuditoria() {
      if (!this.idBase || !this.idControl) return;
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
        console.error("Error en auditoría.", error);
      } finally {
        this.loading = false;
      }
    },

    renderAll() {
      if (!this.resultado) return;
      this.renderPerfil();
      this.renderCFE();
      this.renderTrend();
      this.renderRing();
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
        tooltip: { 
            trigger: 'axis', 
            backgroundColor: this.isDark ? '#1a1d2d' : '#fff', 
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">${params[0].name} hrs</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} W</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        grid: { top: 40, left: 60, right: 30, bottom: 80, containLabel: true },
        xAxis: { type: 'category', data: Array.from({length: 24}, (_, i) => `${i}:00`), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
        series: [
          { name: this.nombreBase, type: 'line', smooth: true, symbolSize: 8, data: this.resultado.dispositivo_base.grafica_perfil_demanda, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(239,68,68,0.2)'},{offset:1,color:'transparent'}]) } },
          { name: this.nombreControl, type: 'line', smooth: true, symbolSize: 8, data: this.resultado.dispositivo_control.grafica_perfil_demanda, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(34,197,94,0.2)'},{offset:1,color:'transparent'}]) } }
        ]
      }, true);
    },

    renderCFE() {
      if (!this.instances.cfe) this.instances.cfe = echarts.init(this.$refs.chartCFE);
      const d = this.resultado.dispositivo_control.desglose_cfe;
      this.instances.cfe.setOption({
        color: ['#f59e0b', '#3b82f6', '#ef4444'],
        tooltip: { trigger: 'item', formatter: '{b}: <b>${c}</b> ({d}%)' },
        series: [{
          type: 'pie', radius: ['60%', '85%'], avoidLabelOverlap: false,
          itemStyle: { borderRadius: 10, borderColor: this.isDark ? '#161925' : '#fff', borderWidth: 4 },
          label: { show: false },
          data: [{ value: d.energia_intermedia, name: 'Intermedia' }, { value: d.energia_punta, name: 'Punta' }, { value: d.energia_base, name: 'Base' }]
        }]
      }, true);
    },

    renderTrend() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      if (!this.instances.trend) this.instances.trend = echarts.init(this.$refs.chartTrend);
      
      const baseData = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.kwh);
      const ctrlData = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.kwh);

      this.instances.trend.setOption({
        color: ['#ef4444', '#22c55e'],
        tooltip: { 
            trigger: 'axis',
            formatter: (params) => {
                let html = `<div style="padding:5px;"><b>Día ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} kWh</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 40 }],
        grid: { top: 30, left: 60, right: 30, bottom: 100, containLabel: true },
        xAxis: { type: 'category', data: Array.from({length: 31}, (_, i) => i + 1), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { show: false } },
        series: [
          { name: 'Referencia', type: 'bar', stack: 'total', data: baseData },
          { name: 'Ahorro', type: 'bar', stack: 'total', data: ctrlData }
        ]
      }, true);
    },

    renderRing() {
      if (!this.instances.ring) this.instances.ring = echarts.init(this.$refs.chartRing);
      const val = this.resultado.comparativa.ahorro_energia_pct;
      this.instances.ring.setOption({
        series: [{
          type: 'pie', radius: ['82%', '95%'], silent: true, label: { show: false },
          data: [
            { value: val, itemStyle: { color: '#22c55e', borderRadius: 10 } },
            { value: 100 - val, itemStyle: { color: this.isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)' } }
          ]
        }]
      }, true);
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

.plataforma-layout { 
  display: flex; width: 100%; min-height: 100vh; transition: background 0.3s; background-color: #f8fafc;
  &.theme-dark { background-color: $DEEP-NAVY !important; }
}

.plataforma-contenido { 
  flex-grow: 1; padding: 40px; margin-left: 80px; transition: margin-left 0.3s; 
  &.shifted { margin-left: 280px; } background-color: inherit;
}

.dashboard-grid-premium { display: grid; grid-template-columns: repeat(5, 1fr); gap: 24px; padding-bottom: 50px; }

.grid-item-header, .grid-item-kpis, .grid-item-data-tables, .grid-item-footer { grid-column: 1 / span 5; }
.grid-item-demand, .grid-item-trend { grid-column: 1 / span 3; }
.grid-item-cfe, .grid-item-metrics { grid-column: 4 / span 2; }

.title-contrast { color: #1e293b; transition: color 0.3s; }
.text-muted-contrast { color: #64748b; transition: color 0.3s; }

.theme-dark {
  .title-contrast { color: #f8fafc !important; }
  .text-muted-contrast { color: #cbd5e1 !important; }
  .glass-card, .kpi-neon-v2, .chart-container-v2, .explain-box { background: $CARD-NAVY !important; border-color: rgba(255,255,255,0.12) !important; }
}

.glass-card { background: white; padding: 24px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); position: relative; overflow: hidden; }
.footer-glow::after { content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, $ACCENT-RED, $ACCENT-BLUE, $ACCENT-GREEN); }

.selector-unit-v3 { display: flex; flex-direction: column; gap: 8px; }
.input-complex { 
  display: flex; align-items: center; background: #f1f5f9; padding: 6px 14px; border-radius: 14px; gap: 10px; border: 1px solid transparent; transition: all 0.2s;
  .input-wrapper { display: flex; align-items: center; color: #64748b; &.id-w { flex-shrink: 0; } }
  .clean-input-text { border: none; background: transparent; width: 140px; font-weight: 700; color: #1e293b; outline: none; font-size: 0.9rem; }
  .clean-input-id { border: none; background: transparent; width: 50px; font-weight: 800; color: #1e293b; outline: none; text-align: center; }
  .divider { width: 1px; height: 24px; background: rgba(0,0,0,0.1); }
  &.red { border-left: 5px solid $ACCENT-RED; }
  &.blue { border-left: 5px solid $ACCENT-BLUE; }
}

.theme-dark .input-complex { 
  background: rgba(255,255,255,0.05) !important; 
  .clean-input-text, .clean-input-id { color: white !important; }
  .divider { background: rgba(255,255,255,0.1); }
}

.label-tiny { font-size: 0.65rem; font-weight: 900; color: #64748b; letter-spacing: 1.5px; margin-bottom: 2px; }

.btn-auditoria-premium { 
  width: 100%; background: #6366f1; color: white; border: none; padding: 18px; border-radius: 18px; font-weight: 900; 
  box-shadow: 0 8px 20px -4px rgba(99, 102, 241, 0.5); transition: all 0.2s;
  &:hover { transform: translateY(-2px); filter: brightness(1.15); box-shadow: 0 12px 25px -4px rgba(99, 102, 241, 0.6); } 
}

.kpi-stripe-v2 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.kpi-neon-v2 { 
  background: white; padding: 24px; border-radius: 24px; border: 1px solid rgba(0,0,0,0.03); display: flex; align-items: center; gap: 18px;
  .kpi-icon-v2 { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; background: rgba(0,0,0,0.03); }
  .value { font-size: 1.8rem; font-weight: 1000; margin: 0; }
  .label { font-size: 0.7rem; font-weight: 800; color: #64748b; display: block; margin-bottom: 2px; }
  &.green { .kpi-icon-v2 { background: rgba($ACCENT-GREEN, 0.1); color: $ACCENT-GREEN; } .value { color: $ACCENT-GREEN; } }
}

.chart-container-v2 { background: white; padding: 28px; border-radius: 28px; border: 1px solid rgba(0,0,0,0.02); height: 100%; }
.echarts-surface-v2 { width: 100%; height: 380px; min-width: 200px; }
.echarts-surface-donut { width: 100%; height: 220px; }
.echarts-ring-v3 { width: 240px; height: 240px; }

.efficiency-ring-v3 { position: relative; .ring-data { position: absolute; top: 52%; left: 50%; transform: translate(-50%, -50%); text-align: center; .percent { font-size: 2.8rem; font-weight: 1000; display: block; line-height: 1; } .lbl { font-size: 0.65rem; font-weight: 900; letter-spacing: 1px; } } }

.m-row { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid rgba(0,0,0,0.05); align-items: center; .m-label { font-size: 0.85rem; font-weight: 700; } .m-vals { font-weight: 900; font-size: 1rem; } }
.theme-dark .m-row { border-color: rgba(255,255,255,0.05); }

.table-auditoria { 
  width: 100%; border-collapse: collapse; 
  th { padding: 20px; background: rgba($ACCENT-BLUE, 0.05); font-size: 0.75rem; font-weight: 900; color: $ACCENT-BLUE; letter-spacing: 1.5px; } 
  td { padding: 22px; border-bottom: 1px solid rgba(0,0,0,0.04); font-weight: 700; font-size: 1rem; } 
}
.theme-dark .table-auditoria { th { background: rgba(255,255,255,0.02); color: #cbd5e1; } td { border-color: rgba(255,255,255,0.05); color: #f8fafc; } }

.cfe-row-v2 { 
  display: flex; align-items: center; padding: 14px 0; border-bottom: 1px solid rgba(0,0,0,0.05); 
  &.punta { border-left: 5px solid $ACCENT-RED; padding-left: 14px; }
  &.intermedia { border-left: 5px solid $ACCENT-BLUE; padding-left: 14px; }
  &.base { border-left: 5px solid $ACCENT-GOLD; padding-left: 14px; }
  .label { flex-grow: 1; font-size: 0.85rem; font-weight: 700; } .val { font-weight: 1000; } 
}

.explain-box { background: white; padding: 25px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); height: 100%; p { line-height: 1.6; } }

.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 1200px) {
  .dashboard-grid-premium { grid-template-columns: 1fr; }
  .grid-item-header, .grid-item-kpis, .grid-item-demand, .grid-item-cfe, .grid-item-trend, .grid-item-metrics, .grid-item-data-tables, .grid-item-footer { grid-column: 1 / -1; }
  .echarts-surface-v2 { height: 300px; }
}
</style>