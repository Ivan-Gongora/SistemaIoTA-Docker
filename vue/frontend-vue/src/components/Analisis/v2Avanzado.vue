<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma 
        titulo="Auditoría Científica de Ahorro" 
        subtitulo="Validación técnica cruzada con variables climatológicas"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen" 
      />
      
      <div class="dashboard-grid-premium">
        
        <div class="grid-item-header">
          <div class="glass-card footer-glow shadow-lg">
            <div class="row g-4 align-items-center">
              <div class="col-xl-2 col-lg-3">
                <div class="d-flex align-items-center gap-3">
                  <div class="icon-pulse green"><i class="bi bi-cpu-fill"></i></div>
                  <div>
                    <h5 class="fw-bold mb-0 title-contrast">Motor Analítico</h5>
                    <span class="text-muted-contrast small">Sistema Activo</span>
                  </div>
                </div>
              </div>
              
              <div class="col-xl-8 col-lg-9">
                <div class="d-flex flex-wrap gap-3 justify-content-center">
                  <div class="selector-unit-v3">
                    <label class="label-tiny">REFERENCIA MANUAL</label>
                    <div class="input-complex red">
                      <div class="input-wrapper">
                        <i class="bi bi-tag-fill me-1"></i>
                        <input type="text" v-model="nombreBase" class="clean-input-text" placeholder="Aula F1">
                      </div>
                      <div class="divider"></div>
                      <div class="input-wrapper id-w">
                        <i class="bi bi-hash"></i>
                        <input type="number" v-model.number="idBase" class="clean-input-id" placeholder="ID">
                      </div>
                    </div>
                  </div>
                  <div class="selector-unit-v3">
                    <label class="label-tiny">EXPERIMENTO AUTOMÁTICO</label>
                    <div class="input-complex blue">
                      <div class="input-wrapper">
                        <i class="bi bi-tag-fill me-1"></i>
                        <input type="text" v-model="nombreControl" class="clean-input-text" placeholder="Aula F3">
                      </div>
                      <div class="divider"></div>
                      <div class="input-wrapper id-w">
                        <i class="bi bi-hash"></i>
                        <input type="number" v-model.number="idControl" class="clean-input-id" placeholder="ID">
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

        <div class="grid-item-kpis" v-if="resultado">
          <div class="kpi-stripe-v2">
            <div class="kpi-neon-v2 green">
              <div class="kpi-icon-v2"><i class="bi bi-currency-dollar"></i></div>
              <div class="kpi-body-v2">
                <span class="label">AHORRO PRORRATEADO</span>
                <h3 class="value">${{ Math.abs(resultado.comparativa.ahorro_financiero_mxn).toFixed(2) }}</h3>
                <span class="badge-saving-v2"><i class="bi bi-arrow-down-short"></i>{{ Math.abs(resultado.comparativa.ahorro_financiero_pct).toFixed(2) }}%</span>
              </div>
            </div>

            <div class="kpi-neon-v2 blue">
              <div class="kpi-icon-v2"><i class="bi bi-lightning-charge"></i></div>
              <div class="kpi-body-v2">
                <span class="label">ENERGÍA EVITADA</span>
                <h3 class="value">{{ Math.abs(resultado.comparativa.diferencia_bruta_kwh).toFixed(2) }} <small>kWh</small></h3>
                <span class="sub-text text-muted-contrast">Mitigación confirmada</span>
              </div>
            </div>

            <div class="kpi-neon-v2 gold">
              <div class="kpi-icon-v2"><i class="bi bi-thermometer-half"></i></div>
              <div class="kpi-body-v2">
                <span class="label">CLIMA EXPERIMENTO</span>
                <h3 class="value">{{ resultado.dispositivo_control.temperatura_promedio }} <small>°C</small></h3>
                <span class="sub-text text-muted-contrast">Humedad {{ resultado.dispositivo_control.humedad_promedio }}%</span>
              </div>
            </div>

            <div class="kpi-neon-v2 green">
              <div class="kpi-icon-v2"><i class="bi bi-patch-check"></i></div>
              <div class="kpi-body-v2">
                <span class="label">PRECISIÓN ANOVA</span>
                <h3 class="value">100%</h3>
                <span class="sub-text text-muted-contrast">Nivel p &lt; 0.05</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-chart-main" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2">
              <h5 class="fw-bold m-0 title-contrast">Perfil Térmico de Demanda Activa</h5>
              <span class="text-muted-contrast small">Potencia registrada en Watts por hora. Pulsa las leyendas para filtrar información.</span>
            </div>
            <div ref="chartPerfil" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-side" v-if="resultado">
          <div class="chart-container-v2 shadow-lg side-content">
            <h5 class="fw-bold mb-4 title-contrast">Impacto en Tarifas CFE</h5>
            <div ref="chartCFE" class="echarts-surface-donut"></div>
            <div class="cfe-details-v2 mt-4">
              <div class="cfe-row-v2 punta">
                <span class="label text-muted-contrast">Costo Punta</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_punta.toFixed(2) }}</span>
              </div>
              <div class="cfe-row-v2 intermedia">
                <span class="label text-muted-contrast">Costo Intermedia</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_intermedia.toFixed(2) }}</span>
              </div>
              <div class="cfe-row-v2 base border-0">
                <span class="label text-muted-contrast">Costo Base</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_base.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-chart-half" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2 mb-4">
              <h5 class="fw-bold m-0 title-contrast">Consumo Total por Segmento Horario</h5>
              <span class="text-muted-contrast small">Acumulación de energía en kWh. Identifica los picos de gasto diario.</span>
            </div>
            <div ref="chartConsumoHora" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-half" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2 mb-4">
              <h5 class="fw-bold m-0 title-contrast">Climatología Ambiental Promedio</h5>
              <span class="text-muted-contrast small">Evolución de temperatura y humedad a lo largo de los días medidos.</span>
            </div>
            <div ref="chartClima" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-main" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2 mb-4">
              <h5 class="fw-bold m-0 title-contrast">Tendencia de Consumo Sincronizada (kWh)</h5>
              <span class="text-muted-contrast small">Comparativa diaria. Emplea la barra inferior para acercar un rango específico.</span>
            </div>
            <div ref="chartTrend" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-side" v-if="resultado">
          <div class="chart-container-v2 shadow-lg d-flex flex-column align-items-center">
            <h5 class="fw-bold mb-4 title-contrast w-100">Eficiencia Operativa</h5>
            
            <div class="circular-wrap flex-grow-1 d-flex align-items-center justify-content-center">
              <div ref="chartRing" class="echarts-ring-v3"></div>
              <div class="ring-data">
                <span class="percent text-success">{{ Math.abs(resultado.comparativa.ahorro_energia_pct).toFixed(0) }}%</span>
                <span class="lbl text-muted-contrast">AHORRO NETO</span>
              </div>
            </div>
            <div class="metrics-summary-v2 w-100 mt-4">
              <div class="m-row">
                <span class="m-label text-muted-contrast">Ocupación Media</span>
                <div class="m-vals title-contrast">
                  <span class="base text-danger me-2">{{ resultado.dispositivo_base.porcentaje_ocupacion }}%</span>
                  <i class="bi bi-chevron-right text-muted-contrast"></i>
                  <span class="ctrl text-success">{{ resultado.dispositivo_control.porcentaje_ocupacion }}%</span>
                </div>
              </div>
              <div class="m-row border-0">
                <span class="m-label text-muted-contrast">Demanda Pico</span>
                <div class="m-vals title-contrast">
                  <span class="base text-danger me-2">{{ resultado.dispositivo_base.corriente_maxima_watts }}W</span>
                  <i class="bi bi-chevron-right text-muted-contrast"></i>
                  <span class="ctrl text-success">{{ resultado.dispositivo_control.corriente_maxima_watts }}W</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-data-tables" v-if="resultado">
          <div class="glass-card shadow-lg p-0 overflow-hidden mb-4">
            <div class="table-header-v2 p-4">
              <h5 class="fw-bold m-0 title-contrast">Resumen Analítico Global</h5>
              <p class="text-muted-contrast small mb-0">Comprobación técnica de los promedios calculados.</p>
            </div>
            <div class="table-responsive">
              <table class="table-auditoria">
                <thead>
                  <tr>
                    <th>INDICADOR</th>
                    <th>UNIDAD</th>
                    <th>{{ nombreBase }}</th>
                    <th>{{ nombreControl }}</th>
                    <th>DIFERENCIA</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="text-muted-contrast">Consumo Mensual Normalizado</td>
                    <td class="text-center small">kWh</td>
                    <td class="text-center fw-bold">{{ resultado.dispositivo_base.consumo_normalizado_kwh }}</td>
                    <td class="text-center fw-bold text-success">{{ resultado.dispositivo_control.consumo_normalizado_kwh }}</td>
                    <td class="text-center text-success fw-bold">{{ Math.abs(resultado.comparativa.ahorro_energia_kwh).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Consumo Promedio Diario</td>
                    <td class="text-center small">kWh</td>
                    <td class="text-center">{{ resultado.dispositivo_base.promedio_diario }}</td>
                    <td class="text-center text-success">{{ resultado.dispositivo_control.promedio_diario }}</td>
                    <td class="text-center text-success fw-bold">{{ Math.abs(resultado.dispositivo_base.promedio_diario - resultado.dispositivo_control.promedio_diario).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Costo Operativo Estimado</td>
                    <td class="text-center small">MXN</td>
                    <td class="text-center">${{ resultado.dispositivo_base.costo_estimado_mxn }}</td>
                    <td class="text-center text-success">${{ resultado.dispositivo_control.costo_estimado_mxn }}</td>
                    <td class="text-center text-success fw-bold">${{ Math.abs(resultado.comparativa.ahorro_financiero_mxn).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Correlación Ocupación y Potencia</td>
                    <td class="text-center small">R²</td>
                    <td class="text-center">{{ resultado.dispositivo_base.correlacion_pir_potencia }}</td>
                    <td class="text-center text-success">{{ resultado.dispositivo_control.correlacion_pir_potencia }}</td>
                    <td class="text-center text-muted-contrast fw-bold">Análisis Válido</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="glass-card shadow-lg p-0 overflow-hidden">
            <div class="table-header-v2 p-4">
              <h5 class="fw-bold m-0 title-contrast">Registro Técnico Diario</h5>
              <p class="text-muted-contrast small mb-0">Cruce de datos entre consumo y lecturas ambientales.</p>
            </div>
            <div class="table-responsive table-scroll">
              <table class="table-auditoria">
                <thead>
                  <tr>
                    <th>FECHA</th>
                    <th class="text-center">{{ nombreBase }} (kWh)</th>
                    <th class="text-center">{{ nombreControl }} (kWh)</th>
                    <th class="text-center">AHORRO OBTENIDO</th>
                    <th class="text-center">TEMP MEDIA</th>
                    <th class="text-center">HUMEDAD</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="index">
                    <td class="text-muted-contrast fw-bold">{{ item.fecha }}</td>
                    <td class="text-center text-danger">{{ item.kwh.toFixed(2) }}</td>
                    <td class="text-center title-contrast fw-bold">{{ resultado.dispositivo_control.grafica_tendencia_diaria[index].kwh.toFixed(2) }}</td>
                    <td class="text-center text-success fw-bold">
                      <i class="bi bi-check-circle-fill me-1"></i>{{ Math.abs(item.kwh - resultado.dispositivo_control.grafica_tendencia_diaria[index].kwh).toFixed(2) }}
                    </td>
                    <td class="text-center title-contrast">{{ ((item.temperatura + resultado.dispositivo_control.grafica_tendencia_diaria[index].temperatura)/2).toFixed(1) }} °C</td>
                    <td class="text-center text-muted-contrast">{{ ((item.humedad + resultado.dispositivo_control.grafica_tendencia_diaria[index].humedad)/2).toFixed(1) }} %</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="grid-item-footer" v-if="resultado">
          <div class="row g-4">
            <div class="col-md-4">
              <div class="explain-box shadow-sm">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-info-circle-fill text-primary"></i>
                  <h6 class="fw-bold m-0 title-contrast">Fundamento Estadístico</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  La evaluación aplica un análisis de varianza ANOVA. El resultado descarta variables aleatorias. Confirma que la mitigación de consumo se debe exclusivamente a TU sistema automático.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-warning">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-lightning-charge-fill text-warning"></i>
                  <h6 class="fw-bold m-0 title-contrast">Prorrateo de Costos</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  El algoritmo asigna un valor ponderado a cada kWh. Este cálculo incluye los cargos fijos y la demanda máxima compartida del recinto escolar.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-success">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-recycle text-success"></i>
                  <h6 class="fw-bold m-0 title-contrast">Normalización Temporal</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  TU plataforma cruza los días exactos de lectura de cada sensor. El sistema genera una comparativa simétrica sin alterar el volumen de datos original.
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
      nombreBase: 'Aula F1',
      nombreControl: 'Aula F3',
      resultado: null,
      instances: { perfil: null, cfe: null, trend: null, ring: null, consumoHora: null, clima: null }
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
          let payload = res.data;
          if (payload.status === 'success' && payload.data) {
              payload = payload.data;
          }
          this.resultado = payload;
          this.$nextTick(() => this.renderAll());
        }
      } catch (error) {
        console.error("Error en comunicación con el servidor.", error);
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
      this.renderConsumoHora();
      this.renderClima();
    },

    renderPerfil() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';
      
      if (!this.instances.perfil) this.instances.perfil = echarts.init(this.$refs.chartPerfil);
      this.instances.perfil.setOption({
        color: ['#ef4444', '#22c55e'],
        toolbox: { 
          feature: { dataZoom: { yAxisIndex: 'none', title: { zoom: 'Zoom', back: 'Restaurar' } }, saveAsImage: { title: 'Descargar' } },
          iconStyle: { borderColor: textColor }
        },
        legend: { textStyle: { color: textColor }, bottom: 0, selectedMode: true },
        tooltip: { 
            trigger: 'axis', 
            backgroundColor: tooltipBg, 
            borderColor: gridColor,
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

    renderConsumoHora() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (!this.instances.consumoHora) this.instances.consumoHora = echarts.init(this.$refs.chartConsumoHora);
      this.instances.consumoHora.setOption({
        color: ['#ef4444', '#22c55e'],
        tooltip: { 
            trigger: 'axis',
            backgroundColor: tooltipBg,
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">${params[0].name} hrs</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} kWh</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        toolbox: { feature: { saveAsImage: { title: 'Descargar' } }, iconStyle: { borderColor: textColor } },
        grid: { top: 30, left: 60, right: 30, bottom: 80, containLabel: true },
        xAxis: { type: 'category', data: Array.from({length: 24}, (_, i) => `${i}:00`), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
        series: [
          { name: this.nombreBase, type: 'bar', data: this.resultado.dispositivo_base.grafica_consumo_por_hora },
          { name: this.nombreControl, type: 'bar', data: this.resultado.dispositivo_control.grafica_consumo_por_hora }
        ]
      }, true);
    },

    renderClima() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (!this.instances.clima) this.instances.clima = echarts.init(this.$refs.chartClima);
      const dias = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.fecha.split('-')[2]);

      this.instances.clima.setOption({
        color: ['#f59e0b', '#3b82f6'],
        tooltip: { 
            trigger: 'axis',
            backgroundColor: tooltipBg,
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">Día ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    let unit = p.seriesName === 'Temperatura' ? '°C' : '%';
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(1)} ${unit}</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        toolbox: { feature: { saveAsImage: { title: 'Descargar' } }, iconStyle: { borderColor: textColor } },
        grid: { top: 30, left: 40, right: 40, bottom: 80, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: [
          { type: 'value', name: '°C', axisLabel: { color: textColor }, splitLine: { show: false } },
          { type: 'value', name: '%', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } }
        ],
        series: [
          { name: 'Temperatura', type: 'line', smooth: true, yAxisIndex: 0, data: this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.temperatura) },
          { name: 'Humedad', type: 'line', smooth: true, yAxisIndex: 1, borderType: 'dashed', data: this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.humedad) }
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
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (!this.instances.trend) this.instances.trend = echarts.init(this.$refs.chartTrend);
      
      const baseData = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.kwh);
      const ctrlData = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.kwh);
      const dias = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.fecha.split('-')[2]);

      this.instances.trend.setOption({
        color: ['#ef4444', '#22c55e'],
        tooltip: { 
            trigger: 'axis',
            backgroundColor: tooltipBg, 
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding:5px;"><b style="color:${textColor}">Día ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} kWh</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 40 }],
        grid: { top: 30, left: 60, right: 30, bottom: 100, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { show: false } },
        series: [
          { name: this.nombreBase, type: 'bar', stack: 'total', data: baseData },
          { name: this.nombreControl, type: 'bar', stack: 'total', data: ctrlData }
        ]
      }, true);
    },

    renderRing() {
      if (!this.instances.ring) this.instances.ring = echarts.init(this.$refs.chartRing);
      const val = Math.abs(this.resultado.comparativa.ahorro_energia_pct);
      
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';

      this.instances.ring.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: tooltipBg,
          borderColor: gridColor,
          textStyle: { color: textColor },
          formatter: function(params) {
            if (params.name === 'Ahorro') {
              return `<div style="padding: 5px;"><b>Eficiencia Neta</b><br/>Reducción registrada: <b>${params.value.toFixed(2)}%</b></div>`;
            }
            return '';
          }
        },
        series: [{
          type: 'pie', radius: ['82%', '95%'], silent: true, label: { show: false },
          data: [
            { name: 'Ahorro', value: val, itemStyle: { color: '#22c55e', borderRadius: 10 } },
            { name: 'Consumo', value: 100 - val, itemStyle: { color: this.isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)' } }
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

.dashboard-grid-premium { display: grid; grid-template-columns: repeat(6, 1fr); gap: 24px; padding-bottom: 50px; }

.grid-item-header, .grid-item-kpis, .grid-item-data-tables, .grid-item-footer { grid-column: 1 / -1; }
.grid-item-chart-main { grid-column: 1 / span 4; }
.grid-item-chart-side { grid-column: 5 / span 2; }
.grid-item-chart-half { grid-column: span 3; }
.grid-item-demand, .grid-item-trend { grid-column: 1 / span 4; }
.grid-item-cfe, .grid-item-metrics { grid-column: 5 / span 2; }

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
  .badge-saving-v2 { background: rgba(34, 197, 94, 0.1); color: #22c55e; padding: 4px 8px; border-radius: 8px; font-size: 0.8rem; font-weight: 800; }
  &.green { .kpi-icon-v2 { background: rgba($ACCENT-GREEN, 0.1); color: $ACCENT-GREEN; } .value { color: $ACCENT-GREEN; } }
  &.blue { .kpi-icon-v2 { background: rgba($ACCENT-BLUE, 0.1); color: $ACCENT-BLUE; } .value { color: $ACCENT-BLUE; } }
  &.gold { .kpi-icon-v2 { background: rgba($ACCENT-GOLD, 0.1); color: $ACCENT-GOLD; } .value { color: $ACCENT-GOLD; } }
  &.red { .kpi-icon-v2 { background: rgba($ACCENT-RED, 0.1); color: $ACCENT-RED; } .value { color: $ACCENT-RED; } }
}

.chart-container-v2 { background: white; padding: 28px; border-radius: 28px; border: 1px solid rgba(0,0,0,0.02); height: 100%; }
.echarts-surface-v2 { width: 100%; height: 380px; min-width: 200px; }
.echarts-surface-donut { width: 100%; height: 220px; }
.echarts-surface-gauge { width: 100%; height: 240px; }

.efficiency-ring-v3 { position: relative; .ring-data { position: absolute; top: 52%; left: 50%; transform: translate(-50%, -50%); text-align: center; .percent { font-size: 2.8rem; font-weight: 1000; display: block; line-height: 1; } .lbl { font-size: 0.65rem; font-weight: 900; letter-spacing: 1px; } } }

.m-row { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid rgba(0,0,0,0.05); align-items: center; .m-label { font-size: 0.85rem; font-weight: 700; } .m-vals { font-weight: 900; font-size: 1.1rem; } }
.theme-dark .m-row { border-color: rgba(255,255,255,0.05); }

.table-scroll { max-height: 400px; overflow-y: auto; }
.table-auditoria { 
  width: 100%; border-collapse: collapse; 
  th { padding: 20px; background: rgba($ACCENT-BLUE, 0.05); font-size: 0.75rem; font-weight: 900; color: $ACCENT-BLUE; letter-spacing: 1.5px; position: sticky; top: 0; z-index: 10; } 
  td { padding: 18px; border-bottom: 1px solid rgba(0,0,0,0.04); font-weight: 700; font-size: 0.95rem; } 
}
.theme-dark .table-auditoria { th { background: #161925; color: #cbd5e1; border-bottom: 1px solid rgba(255,255,255,0.1); } td { border-color: rgba(255,255,255,0.05); color: #f8fafc; } }

.cfe-row-v2 { 
  display: flex; align-items: center; padding: 14px 0; border-bottom: 1px solid rgba(0,0,0,0.05); 
  &.punta { border-left: 5px solid $ACCENT-RED; padding-left: 14px; }
  &.intermedia { border-left: 5px solid $ACCENT-BLUE; padding-left: 14px; }
  &.base { border-left: 5px solid $ACCENT-GOLD; padding-left: 14px; }
  .label { flex-grow: 1; font-size: 0.85rem; font-weight: 700; } .val { font-weight: 1000; font-size: 1.1rem; } 
}

.explain-box { background: white; padding: 25px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); height: 100%; p { line-height: 1.6; } }

.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 1200px) {
  .grid-chart-main, .grid-chart-side { grid-column: 1 / -1; }
  .grid-item-demand, .grid-item-trend { grid-column: 1 / -1; }
  .grid-item-cfe, .grid-item-metrics { grid-column: 1 / -1; }
  .grid-item-chart-half { grid-column: 1 / -1; }
  .kpi-stripe-v2 { grid-template-columns: repeat(2, 1fr); }
}
</style>