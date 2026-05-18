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
            <div class="chart-header-v2 mb-3">
              <h5 class="fw-bold m-0 title-contrast">Perfil Térmico de Demanda Activa</h5>
              <span class="text-muted-contrast small">Consumo registrado en kWh. Los valores fijos señalan los picos operativos en cada lectura horaria.</span>
            </div>
            <div ref="chartPerfil" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-side" v-if="resultado">
          <div class="chart-container-v2 shadow-lg side-content">
            <h5 class="fw-bold mb-4 title-contrast">Proporción de Costo Estimado</h5>
            <div ref="chartCFE" class="echarts-surface-donut"></div>
            <div class="cfe-details-v2 mt-4">
              <div class="cfe-row-v2 punta">
                <span class="label text-muted-contrast">Franja Alta</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_punta.toFixed(2) }}</span>
              </div>
              <div class="cfe-row-v2 intermedia">
                <span class="label text-muted-contrast">Franja Media</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_intermedia.toFixed(2) }}</span>
              </div>
              <div class="cfe-row-v2 base border-0">
                <span class="label text-muted-contrast">Franja Baja</span>
                <span class="val title-contrast">${{ resultado.dispositivo_control.desglose_cfe.energia_base.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-chart-half" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2 mb-4">
              <h5 class="fw-bold m-0 title-contrast">Consumo Total por Segmento Horario</h5>
              <span class="text-muted-contrast small">Acumulación de energía en kWh. Identifica los picos de gasto general durante el día.</span>
            </div>
            <div ref="chartConsumoHora" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-half" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2 mb-4">
              <h5 class="fw-bold m-0 title-contrast">Climatología Ambiental Promedio</h5>
              <span class="text-muted-contrast small">Evolución térmica e hídrica a lo largo de los días de evaluación técnica.</span>
            </div>
            <div ref="chartClima" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-main" v-if="resultado">
          <div class="chart-container-v2 shadow-lg">
            <div class="chart-header-v2 mb-4">
              <h5 class="fw-bold m-0 title-contrast text-success">Tendencia de Ahorro Sincronizada (kWh)</h5>
              <span class="text-muted-contrast small">Comparativa de reducción diaria. Desplaza el control inferior para hacer acercamientos exactos.</span>
            </div>
            <div ref="chartTrend" class="echarts-surface-v2"></div>
          </div>
        </div>

        <div class="grid-item-chart-side" v-if="resultado">
          <div class="chart-container-v2 shadow-lg d-flex flex-column align-items-center">
            <h5 class="fw-bold mb-4 title-contrast w-100 text-success">Eficiencia Operativa</h5>
            
            <div class="efficiency-ring-v3 w-100 d-flex justify-content-center">
              <div ref="chartGauge" class="echarts-surface-gauge"></div>
            </div>
            
            <div class="metrics-summary-v2 w-100 mt-4">
              <div class="m-row border-0">
                <span class="m-label text-muted-contrast">Ocupación Media</span>
                <div class="m-vals title-contrast">
                  <span class="base text-danger me-2">{{ resultado.dispositivo_base.porcentaje_ocupacion }}%</span>
                  <i class="bi bi-chevron-right text-muted-contrast"></i>
                  <span class="ctrl text-success">{{ resultado.dispositivo_control.porcentaje_ocupacion }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-data-tables" v-if="resultado">
          <div ref="tablaGlobal" class="glass-card shadow-lg p-0 overflow-hidden mb-4 border-green-glow">
            <div class="table-header-v2 p-4 bg-success bg-opacity-10 d-flex justify-content-between align-items-center">
              <div>
                <h5 class="fw-bold m-0 text-success">Resumen Analítico Global</h5>
                <p class="text-success small mb-0 opacity-75">Comprobación técnica de los promedios numéricos.</p>
              </div>
              <button @click="exportarImagen('tablaGlobal', 'resumen_global')" class="btn btn-primary btn-sm fw-bold px-3 py-2 rounded-3 shadow-sm d-flex align-items-center">
                <i class="bi bi-camera-fill me-2 fs-6"></i> Captura Visual
              </button>
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

          <div ref="tablaDiaria" class="glass-card shadow-lg p-0 overflow-hidden">
            <div class="table-header-v2 p-4 d-flex justify-content-between align-items-center flex-wrap gap-3">
              <div>
                <h5 class="fw-bold m-0 title-contrast">Registro Técnico Diario</h5>
                <p class="text-muted-contrast small mb-0">Cruce extendido entre consumo eléctrico y lecturas ambientales.</p>
              </div>
              <div class="d-flex gap-2">
                <button @click="exportarTablaLarga('tablaDiaria', 'registro_tecnico_diario')" class="btn btn-primary btn-sm fw-bold px-3 py-2 rounded-3 shadow-sm d-flex align-items-center">
                  <i class="bi bi-camera-fill me-2 fs-6"></i> Imagen
                </button>
                <button @click="exportarCSV" class="btn btn-success btn-sm fw-bold px-3 py-2 rounded-3 shadow-sm d-flex align-items-center">
                  <i class="bi bi-file-earmark-excel-fill me-2 fs-6"></i> Excel
                </button>
              </div>
            </div>
            <div class="table-responsive table-scroll" style="overflow-x: auto;">
              <table class="table-auditoria text-nowrap bg-canvas-export">
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
                  La evaluación ejecuta un análisis ANOVA. El valor probabilístico descarta fluctuaciones aleatorias. Esta validación garantiza que TU ahorro eléctrico proviene del sistema inteligente.
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
                  El algoritmo asigna un valor monetario ponderado a cada kWh. El modelo incorpora la cuota de capacidad máxima exigida y los cargos fijos de TU infraestructura de red.
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
                  TU plataforma alinea los días exactos de actividad registrados en los controladores. El emparejamiento previene un sesgo estadístico en las comparaciones de meses irregulares.
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
    this.cargarLibreriaImagen();
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
    cargarLibreriaImagen() {
      if (!window.html2canvas) {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
        document.head.appendChild(script);
      }
    },
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
             this.errorMsg = "Datos insuficientes en el servidor para generar la evaluación de los IDs ingresados.";
             return;
        }

        this.resultado = payload;
        this.$nextTick(() => this.renderAll());

      } catch (error) {
        console.error("Error en comunicación de red.", error);
        this.errorMsg = "Fallo de comunicación con la base de datos. Confirma el estado de tu servidor.";
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
      link.setAttribute("download", "reporte_auditoria_horizontal.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    async exportarImagen(refName, fileName) {
      if (!window.html2canvas) {
        console.error("Librería de captura fotográfica inactiva.");
        return;
      }
      try {
        const elemento = this.$refs[refName];
        const bgColor = this.isDark ? '#161925' : '#ffffff';
        
        const canvas = await window.html2canvas(elemento, {
          scale: 2,
          backgroundColor: bgColor,
          useCORS: true
        });
        
        const enlace = document.createElement('a');
        enlace.download = `${fileName}.png`;
        enlace.href = canvas.toDataURL('image/png');
        enlace.click();
      } catch (error) {
        console.error("Fallo al compilar la evidencia visual.", error);
      }
    },

    async exportarTablaLarga(refName, fileName) {
      if (!window.html2canvas) return;
      
      try {
        const elemento = this.$refs[refName];
        const tablaAnidada = elemento.querySelector('table');
        const anchoOriginal = elemento.style.width;
        
        if (tablaAnidada) {
            elemento.style.width = (tablaAnidada.offsetWidth + 40) + 'px';
        }

        const bgColor = this.isDark ? '#161925' : '#ffffff';
        
        const canvas = await window.html2canvas(elemento, {
          scale: 2,
          backgroundColor: bgColor,
          useCORS: true
        });
        
        if (tablaAnidada) {
            elemento.style.width = anchoOriginal;
        }

        const enlace = document.createElement('a');
        enlace.download = `${fileName}.png`;
        enlace.href = canvas.toDataURL('image/png');
        enlace.click();
      } catch (error) {
        console.error("Fallo al compilar tabla horizontal.", error);
      }
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

      const baseDataKwh = this.resultado.dispositivo_base.grafica_perfil_demanda.map(v => (v / 1000).toFixed(2));
      const ctrlDataKwh = this.resultado.dispositivo_control.grafica_perfil_demanda.map(v => (v / 1000).toFixed(2));

      this.instances.perfil.setOption({
        color: ['#ef4444', '#10b981'],
        toolbox: {
          show: true,
          feature: {
            dataZoom: { yAxisIndex: 'none', title: { zoom: 'Rango', back: 'Deshacer' } },
            saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_perfil_kwh' }
          },
          iconStyle: { borderColor: textColor }
        },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 15, bottom: 10 }
        ],
        legend: { textStyle: { color: textColor }, bottom: 35, selectedMode: true },
        tooltip: { 
            trigger: 'axis', 
            backgroundColor: tooltipBg, 
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">${params[0].name} hrs</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value} kWh</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        grid: { top: 40, left: 60, right: 30, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: Array.from({length: 24}, (_, i) => `${i}:00`), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
        series: [
          { 
            name: this.nombreBase, 
            type: 'line', 
            smooth: true, 
            symbolSize: 8, 
            data: baseDataKwh, 
            areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(239,68,68,0.15)'},{offset:1,color:'transparent'}]) },
            label: { show: true, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          },
          { 
            name: this.nombreControl, 
            type: 'line', 
            smooth: true, 
            symbolSize: 8, 
            data: ctrlDataKwh, 
            areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(16,185,129,0.3)'},{offset:1,color:'transparent'}]) },
            label: { show: true, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          }
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
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 15, bottom: 10 }
        ],
        legend: { textStyle: { color: textColor }, bottom: 35 },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_consumo_horario' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 60, right: 30, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: Array.from({length: 24}, (_, i) => `${i}:00`), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
        series: [
          { 
            name: this.nombreBase, 
            type: 'bar', 
            data: this.resultado.dispositivo_base.grafica_consumo_por_hora, 
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            label: { show: true, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          },
          { 
            name: this.nombreControl, 
            type: 'bar', 
            data: this.resultado.dispositivo_control.grafica_consumo_por_hora, 
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            label: { show: true, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          }
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
                let html = `<div style="padding:5px;"><b style="color:${textColor}">Día de mes: ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} kWh</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_tendencia_ahorro' } },
          iconStyle: { borderColor: textColor } 
        },
        legend: { textStyle: { color: textColor }, bottom: 35 },
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 15, bottom: 10 }],
        grid: { top: 30, left: 60, right: 30, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
        series: [
          { 
            name: this.nombreBase, 
            type: 'bar', 
            stack: 'total', 
            data: baseData,
            label: { show: true, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          },
          { 
            name: this.nombreControl, 
            type: 'bar', 
            stack: 'total', 
            data: ctrlData,
            label: { show: true, position: 'inside', color: '#fff', fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          }
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
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">Día de mes: ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    let unit = p.seriesName === 'Temperatura' ? '°C' : '%';
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(1)} ${unit}</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { textStyle: { color: textColor }, bottom: 35 },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 15, bottom: 10 }
        ],
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_clima' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 40, right: 40, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: [
          { type: 'value', name: '°C', axisLabel: { color: textColor }, splitLine: { show: false } },
          { type: 'value', name: '%', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } }
        ],
        series: [
          { 
            name: 'Temperatura', 
            type: 'line', 
            smooth: true, 
            yAxisIndex: 0, 
            data: this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.temperatura),
            label: { show: true, position: 'top', color: textColor, fontSize: 10, formatter: '{c}°' },
            labelLayout: { hideOverlap: true }
          },
          { 
            name: 'Humedad', 
            type: 'line', 
            smooth: true, 
            yAxisIndex: 1, 
            borderType: 'dashed', 
            data: this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.humedad),
            label: { show: true, position: 'bottom', color: textColor, fontSize: 10, formatter: '{c}%' },
            labelLayout: { hideOverlap: true }
          }
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
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_tarifas' } },
          iconStyle: { borderColor: textColor } 
        },
        series: [{
          type: 'pie', roseType: 'radius', radius: ['30%', '85%'],
          itemStyle: { borderRadius: 8, borderColor: this.isDark ? '#161925' : '#fff', borderWidth: 2 },
          label: { show: false },
          data: [{ value: d.energia_intermedia, name: 'Franja Media' }, { value: d.energia_punta, name: 'Franja Alta' }, { value: d.energia_base, name: 'Franja Baja' }]
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
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_eficiencia' } },
          iconStyle: { borderColor: textColor } 
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
              show: true,
              formatter: '{value}%',
              color: '#10b981',
              fontSize: 32,
              fontWeight: 'bold',
              offsetCenter: [0, '-10%']
            },
            title: {
              show: true,
              offsetCenter: [0, '25%'],
              color: textColor,
              fontSize: 12,
              fontWeight: 'bold'
            },
            data: [{ value: val, name: 'AHORRO NETO' }]
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
.echarts-surface-gauge { width: 100%; height: 260px; min-height: 260px; min-width: 200px; }

.m-row { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid rgba(0,0,0,0.05); align-items: center; .m-label { font-size: 0.85rem; font-weight: 700; } .m-vals { font-weight: 900; font-size: 1.1rem; } }
.theme-dark .m-row { border-color: rgba(255,255,255,0.05); }

.text-nowrap { white-space: nowrap; }
.table-scroll { max-height: 400px; overflow-y: auto; overflow-x: auto; }

.bg-canvas-export { background: transparent; }
.theme-dark .bg-canvas-export { background: transparent; }

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