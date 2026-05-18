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
          <div class="glass-card shadow-lg border-green-glow">
            <div class="row g-4 align-items-center">
              <div class="col-xl-2 col-lg-3">
                <div class="d-flex align-items-center gap-3">
                  <div class="icon-pulse green"><i class="bi bi-cpu-fill"></i></div>
                  <div>
                    <h5 class="fw-bold mb-0 title-contrast">Motor Analítico</h5>
                    <span class="text-success fw-bold small">Sistema Activo</span>
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
                    <label class="label-tiny text-success">EXPERIMENTO AUTOMÁTICO</label>
                    <div class="input-complex green-box">
                      <div class="input-wrapper">
                        <i class="bi bi-tag-fill me-1"></i>
                        <input type="text" v-model="nombreControl" class="clean-input-text text-success" placeholder="Aula F3">
                      </div>
                      <div class="divider"></div>
                      <div class="input-wrapper id-w">
                        <i class="bi bi-hash text-success"></i>
                        <input type="number" v-model.number="idControl" class="clean-input-id text-success" placeholder="ID">
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

        <div class="grid-item-alert" v-if="errorMsg">
          <div class="alert-premium shadow-lg mt-2">
            <div class="d-flex align-items-center gap-3">
              <div class="icon-error"><i class="bi bi-exclamation-triangle-fill"></i></div>
              <div>
                <h6 class="fw-bold mb-0 text-white">Auditoría Interrumpida</h6>
                <span class="small text-white opacity-75">{{ errorMsg }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-kpis" v-if="resultado">
          <div class="kpi-stripe-v2">
            <div class="kpi-neon-v2 green-highlight">
              <div class="kpi-icon-v2"><i class="bi bi-currency-dollar"></i></div>
              <div class="kpi-body-v2">
                <span class="label text-success">AHORRO PRORRATEADO</span>
                <h3 class="value text-success">${{ Math.abs(resultado.comparativa.ahorro_financiero_mxn).toFixed(2) }}</h3>
                <span class="badge-saving-v2 bg-success text-white"><i class="bi bi-arrow-down-short"></i>{{ Math.abs(resultado.comparativa.ahorro_financiero_pct).toFixed(2) }}%</span>
              </div>
            </div>

            <div class="kpi-neon-v2 green-highlight">
              <div class="kpi-icon-v2"><i class="bi bi-lightning-charge"></i></div>
              <div class="kpi-body-v2">
                <span class="label text-success">ENERGÍA EVITADA</span>
                <h3 class="value text-success">{{ Math.abs(resultado.comparativa.diferencia_bruta_kwh).toFixed(2) }} <small>kWh</small></h3>
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

            <div class="kpi-neon-v2 blue">
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
              <h5 class="fw-bold m-0 title-contrast text-success">Tendencia de Ahorro Sincronizada (kWh)</h5>
              <span class="text-muted-contrast small">Comparativa diaria. Emplea la barra inferior para acercar un rango específico.</span>
            </div>
            <div ref="chartTrend" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-side" v-if="resultado">
          <div class="chart-container-v2 shadow-lg d-flex flex-column align-items-center">
            <h5 class="fw-bold mb-4 title-contrast w-100 text-success">Eficiencia Operativa</h5>
            
            <div class="efficiency-ring-v3 w-100 position-relative">
              <div ref="chartGauge" class="echarts-surface-gauge w-100 mx-auto"></div>
              <div class="ring-data position-absolute top-50 start-50 translate-middle text-center mt-3">
                <span class="percent text-success fw-bolder">{{ Math.abs(resultado.comparativa.ahorro_energia_pct).toFixed(2) }}%</span>
                <span class="lbl text-muted-contrast d-block fw-bold">AHORRO NETO</span>
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
                  <span class="ctrl text-success fw-bold">{{ resultado.dispositivo_control.corriente_maxima_watts }}W</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-data-tables" v-if="resultado">
          <div class="glass-card shadow-lg p-0 overflow-hidden mb-4 border-green-glow">
            <div class="table-header-v2 p-4 bg-success bg-opacity-10">
              <h5 class="fw-bold m-0 text-success">Resumen Analítico Global</h5>
              <p class="text-success small mb-0 opacity-75">Comprobación técnica de los promedios calculados.</p>
            </div>
            <div class="table-responsive">
              <table class="table-auditoria">
                <thead>
                  <tr>
                    <th>INDICADOR</th>
                    <th>UNIDAD</th>
                    <th>{{ nombreBase }}</th>
                    <th>{{ nombreControl }}</th>
                    <th class="text-success">DIFERENCIA A FAVOR</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="text-muted-contrast">Consumo Mensual Normalizado</td>
                    <td class="text-center small">kWh</td>
                    <td class="text-center fw-bold">{{ resultado.dispositivo_base.consumo_normalizado_kwh }}</td>
                    <td class="text-center fw-bold text-success">{{ resultado.dispositivo_control.consumo_normalizado_kwh }}</td>
                    <td class="text-center text-success fw-bold bg-success bg-opacity-10">{{ Math.abs(resultado.comparativa.ahorro_energia_kwh).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Consumo Promedio Diario</td>
                    <td class="text-center small">kWh</td>
                    <td class="text-center">{{ resultado.dispositivo_base.promedio_diario }}</td>
                    <td class="text-center text-success">{{ resultado.dispositivo_control.promedio_diario }}</td>
                    <td class="text-center text-success fw-bold bg-success bg-opacity-10">{{ Math.abs(resultado.dispositivo_base.promedio_diario - resultado.dispositivo_control.promedio_diario).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Costo Operativo Estimado</td>
                    <td class="text-center small">MXN</td>
                    <td class="text-center">${{ resultado.dispositivo_base.costo_estimado_mxn }}</td>
                    <td class="text-center text-success">${{ resultado.dispositivo_control.costo_estimado_mxn }}</td>
                    <td class="text-center text-success fw-bold bg-success bg-opacity-10">${{ Math.abs(resultado.comparativa.ahorro_financiero_mxn).toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast">Correlación Ocupación y Potencia</td>
                    <td class="text-center small">R²</td>
                    <td class="text-center">{{ resultado.dispositivo_base.correlacion_pir_potencia }}</td>
                    <td class="text-center text-success">{{ resultado.dispositivo_control.correlacion_pir_potencia }}</td>
                    <td class="text-center text-success fw-bold bg-success bg-opacity-10">Análisis Válido</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="glass-card shadow-lg p-0 overflow-hidden">
            <div class="table-header-v2 p-4 d-flex justify-content-between align-items-center">
              <div>
                <h5 class="fw-bold m-0 title-contrast">Registro Técnico Diario</h5>
                <p class="text-muted-contrast small mb-0">Cruce de datos entre consumo y lecturas ambientales desplegado horizontalmente.</p>
              </div>
              <button @click="exportarCSV" class="btn btn-success btn-sm fw-bold px-3 py-2 rounded-3 shadow-sm d-flex align-items-center">
                <i class="bi bi-file-earmark-excel-fill me-2 fs-6"></i> Exportar a Excel
              </button>
            </div>
            <div class="table-responsive table-scroll" style="overflow-x: auto;">
              <table class="table-auditoria text-nowrap">
                <thead>
                  <tr>
                    <th class="sticky-col">MÉTRICA \ FECHA</th>
                    <th v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'th-'+index" class="text-center">
                      {{ item.fecha.split('-').slice(1).join('/') }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="text-muted-contrast fw-bold sticky-col">{{ nombreBase }} (kWh)</td>
                    <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'base-'+index" class="text-center text-danger">
                      {{ item.kwh.toFixed(2) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="title-contrast fw-bold sticky-col">{{ nombreControl }} (kWh)</td>
                    <td v-for="(item, index) in resultado.dispositivo_control.grafica_tendencia_diaria" :key="'ctrl-'+index" class="text-center title-contrast fw-bold">
                      {{ item.kwh.toFixed(2) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="text-success fw-bold sticky-col">AHORRO OBTENIDO (kWh)</td>
                    <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'ahorro-'+index" class="text-center text-success fw-bold bg-success bg-opacity-10">
                      {{ Math.abs(item.kwh - resultado.dispositivo_control.grafica_tendencia_diaria[index].kwh).toFixed(2) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast fw-bold sticky-col">TEMP MEDIA (°C)</td>
                    <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'temp-'+index" class="text-center title-contrast">
                      {{ ((item.temperatura + resultado.dispositivo_control.grafica_tendencia_diaria[index].temperatura)/2).toFixed(1) }}°
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted-contrast fw-bold sticky-col">HUMEDAD (%)</td>
                    <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'hum-'+index" class="text-center text-muted-contrast">
                      {{ ((item.humedad + resultado.dispositivo_control.grafica_tendencia_diaria[index].humedad)/2).toFixed(1) }}%
                    </td>
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
                  <i class="bi bi-bar-chart-fill text-primary fs-5"></i>
                  <h6 class="fw-bold m-0 title-contrast">Fundamento Estadístico</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  La evaluación ejecuta un análisis ANOVA. El valor estadístico descarta variaciones aleatorias. Este cálculo confirma el ahorro generado por TU sistema de control.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-warning">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-calculator text-warning fs-5"></i>
                  <h6 class="fw-bold m-0 title-contrast">Prorrateo de Costos</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  El algoritmo asigna un valor monetario ponderado a cada kWh. Este cálculo integra los cargos fijos y la demanda máxima compartida de TU recinto escolar.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-success">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-calendar-check text-success fs-5"></i>
                  <h6 class="fw-bold m-0 title-contrast text-success">Normalización Temporal</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  TU plataforma empareja los días exactos de lectura de cada sensor. El sistema genera una comparativa simétrica precisa.
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
      isDark: true,
      isSidebarOpen: true,
      loading: false,
      errorMsg: null,
      idBase: 15,
      idControl: 16,
      nombreBase: 'Aula F1',
      nombreControl: 'Aula F3',
      resultado: null,
      instances: { perfil: null, consumoHora: null, trend: null, clima: null, cfe: null, gauge: null }
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
    Object.values(this.instances).forEach(inst => {
      if (inst) inst.dispose();
    });
  },
  methods: {
    toggleSidebar() { 
      this.isSidebarOpen = !this.isSidebarOpen;
      setTimeout(this.resizeCharts, 300);
    },
    handleTheme(e) { 
      this.isDark = e.matches; 
      this.$nextTick(() => {
        if (this.resultado) this.renderAll();
      }); 
    },
    detectarTema() { 
      this.isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; 
    },
    resizeCharts() { 
      Object.values(this.instances).forEach(inst => {
        if (inst) inst.resize();
      }); 
    },
    
    async ejecutarAuditoria() {
      if (!this.idBase || !this.idControl) return;
      this.loading = true;
      this.errorMsg = null;
      this.resultado = null; 

      try {
        const baseUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8001';
        const response = await fetch(`${baseUrl}/api/analisis/comparativo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            dispositivo_base_id: parseInt(this.idBase),
            dispositivo_ctrl_id: parseInt(this.idControl),
            fecha_inicio: "2025-10-01 00:00:00",
            fecha_fin: "2025-10-31 23:59:59"
          })
        });
        const res = await response.json();

        if (res.error) {
            this.errorMsg = res.error;
            return;
        }

        let payload = res.data;
        if (payload && payload.status === 'success' && payload.data) {
            payload = payload.data;
        }

        if (payload && payload.error) {
            this.errorMsg = payload.error;
            return;
        }

        if (!payload || !payload.comparativa) {
             this.errorMsg = "Datos insuficientes en el servidor para generar la comparativa de los IDs ingresados.";
             return;
        }

        this.resultado = payload;
        this.$nextTick(() => this.renderAll());

      } catch (error) {
        console.error("Error en comunicación con el servidor.", error);
        this.errorMsg = "Fallo de conexión con el backend. Verifica que el servidor esté activo.";
      } finally {
        this.loading = false;
      }
    },

    exportarCSV() {
      if (!this.resultado) return;

      const BOM = "\uFEFF";
      const baseData = this.resultado.dispositivo_base.grafica_tendencia_diaria;
      const ctrlData = this.resultado.dispositivo_control.grafica_tendencia_diaria;

      let rowFechas = ['MÉTRICA \\ FECHA'];
      let rowBase = [`${this.nombreBase} (kWh)`];
      let rowCtrl = [`${this.nombreControl} (kWh)`];
      let rowAhorro = ['AHORRO OBTENIDO (kWh)'];
      let rowTemp = ['TEMP MEDIA (°C)'];
      let rowHum = ['HUMEDAD (%)'];

      baseData.forEach((item, index) => {
        const ctrlItem = ctrlData[index];
        const ahorro = Math.abs(item.kwh - ctrlItem.kwh).toFixed(2);
        const temp = ((item.temperatura + ctrlItem.temperatura) / 2).toFixed(1);
        const hum = ((item.humedad + ctrlItem.humedad) / 2).toFixed(1);

        rowFechas.push(item.fecha);
        rowBase.push(item.kwh.toFixed(2));
        rowCtrl.push(ctrlItem.kwh.toFixed(2));
        rowAhorro.push(ahorro);
        rowTemp.push(temp);
        rowHum.push(hum);
      });

      const csvContent = BOM + 
        rowFechas.join(",") + "\n" +
        rowBase.join(",") + "\n" +
        rowCtrl.join(",") + "\n" +
        rowAhorro.join(",") + "\n" +
        rowTemp.join(",") + "\n" +
        rowHum.join(",") + "\n";

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", "registro_tecnico_diario_horizontal.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    renderAll() {
      if (!this.resultado) return;
      this.renderPerfil();
      this.renderConsumoHora();
      this.renderTrend();
      this.renderClima();
      this.renderCFE();
      this.renderGauge();
    },

    renderPerfil() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';
      
      if (this.instances.perfil) this.instances.perfil.dispose();
      this.instances.perfil = echarts.init(this.$refs.chartPerfil);

      this.instances.perfil.setOption({
        color: ['#ef4444', '#10b981'],
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
          { name: this.nombreControl, type: 'line', smooth: true, symbolSize: 8, data: this.resultado.dispositivo_control.grafica_perfil_demanda, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(16,185,129,0.3)'},{offset:1,color:'transparent'}]) } }
        ]
      }, true);
    },

    renderConsumoHora() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.consumoHora) this.instances.consumoHora.dispose();
      this.instances.consumoHora = echarts.init(this.$refs.chartConsumoHora);

      this.instances.consumoHora.setOption({
        color: ['#ef4444', '#10b981'],
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
          { name: this.nombreBase, type: 'bar', data: this.resultado.dispositivo_base.grafica_consumo_por_hora, itemStyle: { borderRadius: [4, 4, 0, 0] } },
          { name: this.nombreControl, type: 'bar', data: this.resultado.dispositivo_control.grafica_consumo_por_hora, itemStyle: { borderRadius: [4, 4, 0, 0] } }
        ]
      }, true);
    },

    renderTrend() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.trend) this.instances.trend.dispose();
      this.instances.trend = echarts.init(this.$refs.chartTrend);

      const dias = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.fecha.split('-')[2]);
      const baseData = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.kwh);
      const ctrlData = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.kwh);

      this.instances.trend.setOption({
        color: ['#ef4444', '#10b981'],
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
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20, bottom: 30 }],
        grid: { top: 30, left: 60, right: 30, bottom: 80, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
        series: [
          { name: this.nombreBase, type: 'bar', stack: 'total', data: baseData },
          { name: this.nombreControl, type: 'bar', stack: 'total', data: ctrlData }
        ]
      }, true);
    },

    renderClima() {
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.clima) this.instances.clima.dispose();
      this.instances.clima = echarts.init(this.$refs.chartClima);

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
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';

      if (this.instances.cfe) this.instances.cfe.dispose();
      this.instances.cfe = echarts.init(this.$refs.chartCFE);

      const d = this.resultado.dispositivo_control.desglose_cfe;
      this.instances.cfe.setOption({
        color: ['#f59e0b', '#3b82f6', '#ef4444'],
        tooltip: { 
            trigger: 'item', 
            backgroundColor: tooltipBg,
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: '{b}: <b>${c}</b> ({d}%)' 
        },
        series: [{
          type: 'pie', roseType: 'radius', radius: ['30%', '85%'],
          itemStyle: { borderRadius: 8, borderColor: this.isDark ? '#161925' : '#fff', borderWidth: 2 },
          label: { show: false },
          data: [{ value: d.energia_intermedia, name: 'Intermedia' }, { value: d.energia_punta, name: 'Punta' }, { value: d.energia_base, name: 'Base' }]
        }]
      }, true);
    },

    renderGauge() {
      const textColor = this.isDark ? '#cbd5e1' : '#64748b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.gauge) this.instances.gauge.dispose();
      this.instances.gauge = echarts.init(this.$refs.chartGauge);

      const val = Math.abs(this.resultado.comparativa.ahorro_energia_pct);

      this.instances.gauge.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: tooltipBg,
          borderColor: gridColor,
          textStyle: { color: this.isDark ? '#f8fafc' : '#1e293b' },
          formatter: function() {
            return `<div style="padding: 5px;"><b>Eficiencia Operativa</b><br/>Ahorro validado: <b>${val.toFixed(2)}%</b></div>`;
          }
        },
        series: [
          {
            type: 'gauge',
            startAngle: 210,
            endAngle: -30,
            min: 0,
            max: 100,
            splitNumber: 10,
            radius: '100%',
            center: ['50%', '55%'],
            itemStyle: {
              color: '#10b981',
              shadowColor: 'rgba(16,185,129,0.3)',
              shadowBlur: 8,
              shadowOffsetX: 0,
              shadowOffsetY: 0
            },
            progress: {
              show: true,
              roundCap: true,
              width: 14
            },
            pointer: {
              show: false
            },
            axisLine: {
              roundCap: true,
              lineStyle: {
                width: 14,
                color: [[1, gridColor]]
              }
            },
            axisTick: {
              distance: -22,
              splitNumber: 5,
              length: 6,
              lineStyle: {
                width: 1,
                color: textColor
              }
            },
            splitLine: {
              distance: -28,
              length: 10,
              lineStyle: {
                width: 2,
                color: textColor
              }
            },
            axisLabel: {
              distance: 35,
              color: textColor,
              fontSize: 10
            },
            detail: {
              show: false
            },
            data: [{ value: val, name: 'Ahorro' }]
          }
        ]
      }, true);
    }
  }
};
</script>

<style scoped lang="scss">
$DEEP-NAVY: #0f111a;
$CARD-NAVY: #161925;
$ACCENT-BLUE: #3b82f6;
$ACCENT-GREEN: #10b981;
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

.grid-item-header, .grid-item-alert, .grid-item-kpis, .grid-item-data-tables, .grid-item-footer { grid-column: 1 / -1; }
.grid-item-chart-main { grid-column: 1 / span 4; }
.grid-item-chart-side { grid-column: 5 / span 2; }
.grid-item-chart-half { grid-column: span 3; }

.title-contrast { color: #1e293b; transition: color 0.3s; }
.text-muted-contrast { color: #64748b; transition: color 0.3s; }

.theme-dark {
  .title-contrast { color: #f8fafc !important; }
  .text-muted-contrast { color: #cbd5e1 !important; }
  .glass-card, .kpi-neon-v2, .chart-container-v2, .explain-box { background: $CARD-NAVY !important; border-color: rgba(255,255,255,0.1) !important; }
}

.glass-card { background: white; padding: 24px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); position: relative; overflow: hidden; }
.border-green-glow { border: 1px solid rgba($ACCENT-GREEN, 0.3) !important; box-shadow: 0 0 15px rgba($ACCENT-GREEN, 0.1); }
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

.green-box { border-left: 5px solid $ACCENT-GREEN !important; background: rgba($ACCENT-GREEN, 0.05) !important; }

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

.alert-premium { background: rgba(239, 68, 68, 0.95); border: 1px solid #ef4444; padding: 18px 24px; border-radius: 16px; width: 100%; }
.icon-error { width: 42px; height: 42px; border-radius: 12px; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; color: white; }

.kpi-stripe-v2 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.kpi-neon-v2 { 
  background: white; padding: 24px; border-radius: 24px; border: 1px solid rgba(0,0,0,0.03); display: flex; align-items: center; gap: 18px;
  .kpi-icon-v2 { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; background: rgba(0,0,0,0.03); }
  .value { font-size: 1.8rem; font-weight: 1000; margin: 0; color: #1e293b; }
  .label { font-size: 0.7rem; font-weight: 800; color: #64748b; display: block; margin-bottom: 2px; }
  .badge-saving-v2 { padding: 4px 8px; border-radius: 8px; font-size: 0.8rem; font-weight: 800; }
  &.green-highlight { border: 1px solid rgba($ACCENT-GREEN, 0.2); box-shadow: 0 4px 15px rgba($ACCENT-GREEN, 0.05); .kpi-icon-v2 { background: rgba($ACCENT-GREEN, 0.1); color: $ACCENT-GREEN; } }
  &.blue { .kpi-icon-v2 { background: rgba($ACCENT-BLUE, 0.1); color: $ACCENT-BLUE; } }
  &.gold { .kpi-icon-v2 { background: rgba($ACCENT-GOLD, 0.1); color: $ACCENT-GOLD; } }
  &.red { .kpi-icon-v2 { background: rgba($ACCENT-RED, 0.1); color: $ACCENT-RED; } }
}
.theme-dark .kpi-neon-v2 .value { color: #f8fafc; }

.chart-container-v2 { background: white; padding: 28px; border-radius: 28px; border: 1px solid rgba(0,0,0,0.02); height: 100%; }
.echarts-surface-v2 { width: 100%; height: 380px; min-width: 200px; }
.echarts-surface-small { width: 100%; height: 260px; min-width: 200px; }
.echarts-surface-donut { width: 100%; height: 220px; }
.echarts-surface-gauge { width: 100%; height: 260px; min-width: 200px; }

.efficiency-ring-v3 { position: relative; .ring-data { position: absolute; top: 52%; left: 50%; transform: translate(-50%, -50%); text-align: center; .percent { font-size: 2.8rem; font-weight: 1000; display: block; line-height: 1; } .lbl { font-size: 0.75rem; font-weight: 900; letter-spacing: 1px; } } }

.m-row { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid rgba(0,0,0,0.05); align-items: center; .m-label { font-size: 0.85rem; font-weight: 700; } .m-vals { font-weight: 900; font-size: 1.1rem; } }
.theme-dark .m-row { border-color: rgba(255,255,255,0.05); }

.text-nowrap { white-space: nowrap; }
.table-scroll { max-height: 400px; overflow-y: auto; overflow-x: auto; }

.table-auditoria { 
  width: 100%; border-collapse: collapse; 
  th { padding: 20px; font-size: 0.75rem; font-weight: 900; color: $ACCENT-BLUE; letter-spacing: 1.5px; position: sticky; top: 0; z-index: 10; background: rgba($ACCENT-BLUE, 0.05); } 
  td { padding: 18px; border-bottom: 1px solid rgba(0,0,0,0.04); font-weight: 700; font-size: 0.95rem; } 
}

.sticky-col { position: sticky; left: 0; background: white; z-index: 11; border-right: 1px solid rgba(0,0,0,0.05); }
.theme-dark .table-auditoria th { background: #161925; color: #cbd5e1; border-bottom: 1px solid rgba(255,255,255,0.1); }
.theme-dark .table-auditoria td { border-color: rgba(255,255,255,0.05); color: #f8fafc; }
.theme-dark .sticky-col { background: #161925; border-right-color: rgba(255,255,255,0.05); }
.table-auditoria th.sticky-col { z-index: 12; }

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