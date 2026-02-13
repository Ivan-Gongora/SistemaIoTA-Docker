<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma
        titulo="Resumen Estadístico Energético"
        subtitulo="Análisis de los lotes energéticos seleccionados"
        @toggle-sidebar="toggleSidebar"
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="resumen-estadistico-container">
        
        <div v-if="loading" class="loading-overlay">
          <div class="spinner-border text-primary" role="status"></div>
          <p class="loading-text">Procesando análisis estadístico...</p>
        </div>

        <div v-else-if="error" class="alert-box error">
          <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
        </div>

        <div v-else-if="!lotesCargados || lotesCargados.length === 0" class="alert-box warning">
          <i class="bi bi-info-circle-fill"></i> No hay lotes seleccionados. Por favor regrese a Gestión de Datos.
        </div>

        <div v-else class="dashboard-grid">
          
<div class="actions-bar mb-4 d-flex justify-content-end" v-if="!loading && !error">
  <button @click="exportarExcel" class="btn-export">
    <i class="bi bi-file-earmark-excel-fill"></i> Exportar Reporte
  </button>
</div>

          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-icon"><i class="bi bi-lightning-charge"></i></div>
              <div class="kpi-content">
                <span class="kpi-label">Consumo Promedio</span>
                <span class="kpi-value" :title="formatoNumero(estadisticasBasicas.consumo_promedio_kwh)">
                  {{ formatoNumero(estadisticasBasicas.consumo_promedio_kwh) }} <small>kWh</small>
                </span>
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-icon"><i class="bi bi-cash-coin"></i></div>
              <div class="kpi-content">
                <span class="kpi-label">Costo Promedio</span>
                <span class="kpi-value" :title="formatoMoneda(estadisticasBasicas.costo_promedio_mxn)">
                  {{ formatoMoneda(estadisticasBasicas.costo_promedio_mxn) }}
                </span>
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-icon"><i class="bi bi-graph-up"></i></div>
              <div class="kpi-content">
                <span class="kpi-label">Demanda Máx.</span>
                <span class="kpi-value">
                  {{ formatoNumero(estadisticasBasicas.demanda_maxima_promedio_kw) }} <small>kW</small>
                </span>
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-icon"><i class="bi bi-battery-charging"></i></div>
              <div class="kpi-content">
                <span class="kpi-label">Factor Potencia</span>
                <span class="kpi-value">
                  {{ formatoPorcentaje(estadisticasBasicas.factor_potencia_promedio) }}
                </span>
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-icon"><i class="bi bi-arrow-left-right"></i></div>
              <div class="kpi-content">
                <span class="kpi-label">Corr. Consumo-Costo</span>
                <span class="kpi-value">
                  {{ formatoNumero(estadisticasAnalisis.correlaciones.consumo_costo) }}
                </span>
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-icon"><i class="bi bi-bezier2"></i></div>
              <div class="kpi-content">
                <span class="kpi-label">Corr. Demanda-Consumo</span>
                <span class="kpi-value">
                  {{ formatoNumero(estadisticasAnalisis.correlaciones.demanda_consumo) }}
                </span>
              </div>
            </div>
          </div>

          <div class="charts-row">
            <div class="chart-container">
              <div class="chart-header">
                <h5>Patrón Mensual Promedio</h5>
                <span class="chart-subtitle">Tendencia histórica consolidada</span>
              </div>
              <div class="chart-body">
                <GraficoLineasEvolucion
                  :datos-mensuales="tendenciasMensualesProcesadas"
                  :is-dark="isDark"
                />
              </div>
            </div>

            <div class="chart-container">
              <div class="chart-header">
                <h5>Comparativa Anual</h5>
                <span class="chart-subtitle">Totales por año fiscal</span>
              </div>
              <div class="chart-body">
                <GraficoBarrasComparativas
                  :datos-anuales="estadisticasAnualesProcesadas"
                  :is-dark="isDark"
                />
              </div>
            </div>
          </div>

          <div class="chart-container full-width">
            <div class="chart-header">
              <h5>Evolución de Consumo por Lote</h5>
              <span class="chart-subtitle">Histórico completo detallado</span>
            </div>
            <div class="chart-body large-chart">
              <GraficoEvolucionSeries
                :datos-evolucion="datosEvolucionPorLote"
                :metrica-seleccionada="metricaSeleccionada"
                :is-dark="isDark"
              />
            </div>
          </div>

          <div class="table-container">
            <div class="table-header">
              <h5>Estadísticas Anuales</h5>
            </div>
            <div class="table-responsive-wrapper">
              <table class="custom-table">
                <thead>
                  <tr>
                    <th>Año</th>
                    <th>Consumo Total</th>
                    <th>Consumo Prom.</th>
                    <th>Costo Total</th>
                    <th>Costo Prom.</th>
                    <th>Demanda Máx.</th>
                    <th>Demanda Prom.</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="stat in estadisticasAnalisis.estadisticas_anuales" :key="stat.año">
                    <td class="fw-bold">{{ stat.año }}</td>
                    <td>{{ formatoNumero(stat.consumo_total_kwh_sum) }} kWh</td>
                    <td>{{ formatoNumero(stat.consumo_total_kwh_mean) }} kWh</td>
                    <td>{{ formatoMoneda(stat.costo_total_sum) }}</td>
                    <td>{{ formatoMoneda(stat.costo_total_mean) }}</td>
                    <td>{{ formatoNumero(stat.demanda_maxima_kw_max) }} kW</td>
                    <td>{{ formatoNumero(stat.demanda_maxima_kw_mean) }} kW</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="table-footer" v-if="estadisticasAnalisis.lotes_analizados">
              <i class="bi bi-archive"></i>
              <span>Lotes analizados: {{ estadisticasAnalisis.lotes_analizados.join(', ') }}</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 1. IMPORTAR LIBRERÍA DE EXCEL
import * as XLSX from 'xlsx';

// Componentes de Layout
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

// Componentes específicos
import ResumenCard from '@/components/ResumenCard.vue';
import GraficoBarrasComparativas from '@/components/graficos/GraficoBarrasComparativas.vue';
import GraficoLineasEvolucion from '@/components/graficos/GraficoLineasEvolucion.vue';
import GraficoEvolucionSeries from '@/components/graficos/GraficoEvolucionSeries.vue';

export default {
  name: 'VistaResumenEstadistico',
  components: {
    BarraLateralPlataforma,
    EncabezadoPlataforma,
    ResumenCard,
    GraficoBarrasComparativas,
    GraficoLineasEvolucion,
    GraficoEvolucionSeries,
  },
  data() {
    return {
      isDark: false,
      isSidebarOpen: true,
      lotesCargados: [],
      loading: true,
      error: null,
      
      estadisticasBasicas: {
        total_registros: 0,
        rango_fechas: { inicio: '', fin: '' },
        consumo_promedio_kwh: 0,
        consumo_max_kwh: 0,
        consumo_min_kwh: 0,
        costo_promedio_mxn: 0,
        costo_total_acumulado: 0,
        demanda_maxima_promedio_kw: 0,
        factor_potencia_promedio: 0,
      },
      tendenciasMensuales: [], 
      estadisticasAnalisis: {
        estadisticas_anuales: [],
        patron_mensual: [],
        correlaciones: { consumo_costo: 0, demanda_consumo: 0 },
        lotes_analizados: [],
      },
      metricaSeleccionada: 'consumo_total_kwh', 
    };
  },
  computed: {
    tendenciasMensualesProcesadas() {
        const patronMensual = this.estadisticasAnalisis.patron_mensual;
        if (!patronMensual || patronMensual.length === 0) return [];

        return [
            {
                name: 'Consumo (kWh)',
                data: patronMensual.map(m => ({ mes: m.mes, consumo_total_kwh: m.consumo_total_kwh }))
            },
            {
                name: 'Costo (MXN)',
                data: patronMensual.map(m => ({ mes: m.mes, costo_total: m.costo_total }))
            }
        ];
    },

    estadisticasAnualesProcesadas() {
      const annualData = {};
      this.estadisticasAnalisis.estadisticas_anuales.forEach(stat => {
        if (!annualData[stat.año]) {
          annualData[stat.año] = {
            consumo_total_kwh: 0,
            costo_total: 0,
          };
        }
        annualData[stat.año].consumo_total_kwh += stat.consumo_total_kwh_sum || 0;
        annualData[stat.año].costo_total += stat.costo_total_sum || 0;
      });
      return annualData;
    },

datosEvolucionPorLote() {
  // Validaciones previas
  if (!this.tendenciasMensuales || this.tendenciasMensuales.length === 0) {
    return { labels: [], series: [] };
  }

  // Extraemos todos los periodos del backend (eje X)
  const labels = this.tendenciasMensuales.map(item => item.periodo);

  // Mapeamos los valores de la métrica actual
  const dataValues = this.tendenciasMensuales.map(item => {
    const valor = item[this.metricaSeleccionada];
    return (valor !== undefined && valor !== null) ? valor : 0;
  });

  // Serie consolidada representando el total de los lotes enviados al backend
  return {
    labels: labels,
    series: [
      {
        name: this.lotesCargados.length > 1
          ? 'Total Seleccionado'
          : `Lote ${this.lotesCargados[0]}`,
        data: dataValues,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
      },
    ],
  };
}
,
  },
  
  async mounted() {
    this.detectarTemaSistema();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleThemeChange);
    }
    await this.cargarDatos();
  },
  beforeUnmount() {
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleThemeChange);
    }
  },
  
  methods: {
    toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; },
    handleThemeChange(event) { this.isDark = event.matches; },
    detectarTemaSistema() {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.isDark = true;
      } else {
        this.isDark = false;
      }
    },

    async cargarDatos() {
      this.loading = true;
      this.error = null;

      const lotesQuery = this.$route.query.lotes;
      if (lotesQuery) {
        this.lotesCargados = Array.isArray(lotesQuery) ? lotesQuery : [lotesQuery];
      }

      if (this.lotesCargados.length === 0) {
        this.error = "No se seleccionaron lotes para el análisis. Por favor, regrese y seleccione al menos uno.";
        this.loading = false;
        return;
      }

      const token = localStorage.getItem('accessToken');
      if (!token) {
        this.error = "Error de autenticación. No se pudo obtener el token.";
        this.loading = false;
        this.$router.push('/');
        return;
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      const body = JSON.stringify({ lotes_seleccionados: this.lotesCargados });

      try {
        // 1. Obtener Análisis Histórico
        const historicoResponse = await fetch(`${API_BASE_URL}/api/energetico/analisis/historico`, { 
          method: 'POST',
          headers: headers,
          body: body
        });
        if (!historicoResponse.ok) throw new Error(`Error ${historicoResponse.status} al cargar análisis histórico`);
        
        const historicoData = await historicoResponse.json();
        if (historicoData.status === 'success' && historicoData.data) {
          this.estadisticasBasicas = historicoData.data.estadisticas_basicas || this.estadisticasBasicas;
          this.tendenciasMensuales = historicoData.data.tendencias_mensuales || []; 
        } else {
            console.warn("Respuesta inesperada historico:", historicoData);
            this.error = "Datos históricos incompletos.";
        }

        // 2. Obtener Estadísticas
        const estadisticasResponse = await fetch(`${API_BASE_URL}/api/energetico/analisis/estadisticas`, { 
          method: 'POST',
          headers: headers,
          body: body
        });
        if (!estadisticasResponse.ok) throw new Error(`Error ${estadisticasResponse.status} al cargar estadísticas`);
        
        const estadisticasData = await estadisticasResponse.json();
        if (estadisticasData.status === 'success' && estadisticasData.data) {
          this.estadisticasAnalisis.estadisticas_anuales = estadisticasData.data.estadisticas_anuales || [];
          this.estadisticasAnalisis.patron_mensual = estadisticasData.data.patron_mensual || []; 
          this.estadisticasAnalisis.correlaciones = estadisticasData.data.correlaciones || { consumo_costo: 0, demanda_consumo: 0 };
          this.estadisticasAnalisis.lotes_analizados = estadisticasData.data.lotes_analizados || [];
        } else {
            console.warn("Respuesta inesperada estadisticas:", estadisticasData);
            this.error = "Estadísticas incompletas.";
        }

      } catch (err) {
        console.error("Error carga:", err);
        this.error = "No se pudieron cargar los datos. Verifique conexión.";
      } finally {
        this.loading = false;
      }
    },

    formatoNumero(val) { return val ? Number(val).toLocaleString('es-MX', { maximumFractionDigits: 2 }) : '0'; },
    formatoMoneda(val) { return val ? Number(val).toLocaleString('es-MX', { style: 'currency', currency: 'MXN' }) : '$0.00'; },
    formatoPorcentaje(val) { return val ? Number(val).toFixed(2) + '%' : '0%'; },
    exportarExcel() {
      // 1. Validación previa
      if (!this.lotesCargados.length) {
        alert("No hay datos cargados para exportar.");
        return;
      }

      try {
        const wb = XLSX.utils.book_new();

        // =========================================================
        // HOJA 1: RESUMEN EJECUTIVO (KPIs + Correlaciones)
        // Fuente: estadisticasBasicas (Endpoint 1) y estadisticasAnalisis (Endpoint 2)
        // =========================================================
        const resumenData = [
          ["REPORTE DE ANÁLISIS ENERGÉTICO"],
          ["Generado el:", new Date().toLocaleString()],
          ["Lotes incluidos:", this.lotesCargados.join(", ")],
          [], // Espacio en blanco
          ["INDICADORES CLAVE (KPIs)", "VALOR"],
          ["Consumo Promedio", `${this.formatoNumero(this.estadisticasBasicas.consumo_promedio_kwh)} kWh`],
          ["Consumo Máximo", `${this.formatoNumero(this.estadisticasBasicas.consumo_max_kwh)} kWh`],
          ["Consumo Mínimo", `${this.formatoNumero(this.estadisticasBasicas.consumo_min_kwh)} kWh`],
          ["Costo Promedio", this.formatoMoneda(this.estadisticasBasicas.costo_promedio_mxn)],
          ["Costo Total Acumulado", this.formatoMoneda(this.estadisticasBasicas.costo_total_acumulado)],
          ["Demanda Máxima Prom.", `${this.formatoNumero(this.estadisticasBasicas.demanda_maxima_promedio_kw)} kW`],
          ["Factor de Potencia Prom.", this.formatoPorcentaje(this.estadisticasBasicas.factor_potencia_promedio)],
          ["Total Registros", this.estadisticasBasicas.total_registros],
          [],
          ["ANÁLISIS DE CORRELACIÓN", "COEFICIENTE"],
          ["Consumo vs Costo", this.estadisticasAnalisis.correlaciones.consumo_costo],
          ["Demanda vs Consumo", this.estadisticasAnalisis.correlaciones.demanda_consumo]
        ];
        const wsResumen = XLSX.utils.aoa_to_sheet(resumenData);
        // Ajustar ancho de columnas para que se vea bien
        wsResumen['!cols'] = [{wch: 30}, {wch: 25}];
        XLSX.utils.book_append_sheet(wb, wsResumen, "Resumen Ejecutivo");


        // =========================================================
        // HOJA 2: ESTADÍSTICAS ANUALES
        // Fuente: estadisticasAnalisis.estadisticas_anuales (Endpoint 2)
        // =========================================================
        if (this.estadisticasAnalisis.estadisticas_anuales.length > 0) {
            const datosAnuales = this.estadisticasAnalisis.estadisticas_anuales.map(item => ({
              "Año": item.año,
              "Consumo Total (kWh)": item.consumo_total_kwh_sum,
              "Consumo Prom. (kWh)": item.consumo_total_kwh_mean,
              "Desviación Consumo": item.consumo_total_kwh_std, // Dato extra que vi en tu JSON
              "Costo Total (MXN)": item.costo_total_sum,
              "Costo Prom. (MXN)": item.costo_total_mean,
              "Demanda Máx (kW)": item.demanda_maxima_kw_max,
              "Demanda Prom (kW)": item.demanda_maxima_kw_mean
            }));
            const wsAnual = XLSX.utils.json_to_sheet(datosAnuales);
            wsAnual['!cols'] = [{wch:10}, {wch:20}, {wch:20}, {wch:20}, {wch:18}, {wch:18}, {wch:18}, {wch:18}];
            XLSX.utils.book_append_sheet(wb, wsAnual, "Comparativa Anual");
        }


        // =========================================================
        // HOJA 3: PATRÓN MENSUAL PROMEDIO
        // Fuente: estadisticasAnalisis.patron_mensual (Endpoint 2)
        // =========================================================
        if (this.estadisticasAnalisis.patron_mensual.length > 0) {
            const datosPatron = this.estadisticasAnalisis.patron_mensual.map(item => ({
                "Mes (Num)": item.mes,
                "Consumo Promedio (kWh)": item.consumo_total_kwh,
                "Costo Promedio (MXN)": item.costo_total
            }));
            const wsPatron = XLSX.utils.json_to_sheet(datosPatron);
            wsPatron['!cols'] = [{wch:10}, {wch:25}, {wch:25}];
            XLSX.utils.book_append_sheet(wb, wsPatron, "Patrón Mensual");
        }


        // =========================================================
        // HOJA 4: HISTÓRICO COMPLETO (Evolución)
        // Fuente: tendenciasMensuales (Endpoint 1)
        // =========================================================
        if (this.tendenciasMensuales.length > 0) {
            // Nota: Según tu JSON, tendencias_mensuales solo trae periodo, consumo y costo.
            // No trae demanda ni factor de potencia en este array específico.
            const datosHistoricos = this.tendenciasMensuales.map(item => ({
              "Periodo": item.periodo, // Ej: 2021-01
              "Consumo Total (kWh)": item.consumo_total_kwh,
              "Costo Total (MXN)": item.costo_total
            }));
            const wsHistorico = XLSX.utils.json_to_sheet(datosHistoricos);
            wsHistorico['!cols'] = [{wch:15}, {wch:20}, {wch:20}];
            XLSX.utils.book_append_sheet(wb, wsHistorico, "Histórico Completo");
        }

        // 4. Descargar el archivo
        const fecha = new Date().toISOString().slice(0,10);
        XLSX.writeFile(wb, `Analisis_Energetico_${fecha}.xlsx`);

      } catch (error) {
        console.error("Error al exportar:", error);
        alert("Hubo un error al generar el Excel. Revise la consola para más detalles.");
      }
    }
  //  exportarExcel() {
  //     // 1. Validación previa
  //     if (!this.lotesCargados.length) {
  //       alert("No hay datos cargados para exportar.");
  //       return;
  //     }

  //     try {
  //       const wb = XLSX.utils.book_new();

  //       // =========================================================
  //       // HOJA 1: RESUMEN EJECUTIVO (KPIs + Correlaciones)
  //       // Fuente: estadisticasBasicas (Endpoint 1) y estadisticasAnalisis (Endpoint 2)
  //       // =========================================================
  //       const resumenData = [
  //         ["REPORTE DE ANÁLISIS ENERGÉTICO"],
  //         ["Generado el:", new Date().toLocaleString()],
  //         ["Lotes incluidos:", this.lotesCargados.join(", ")],
  //         [], // Espacio en blanco
  //         ["INDICADORES CLAVE (KPIs)", "VALOR"],
  //         ["Consumo Promedio", `${this.formatoNumero(this.estadisticasBasicas.consumo_promedio_kwh)} kWh`],
  //         ["Consumo Máximo", `${this.formatoNumero(this.estadisticasBasicas.consumo_max_kwh)} kWh`],
  //         ["Consumo Mínimo", `${this.formatoNumero(this.estadisticasBasicas.consumo_min_kwh)} kWh`],
  //         ["Costo Promedio", this.formatoMoneda(this.estadisticasBasicas.costo_promedio_mxn)],
  //         ["Costo Total Acumulado", this.formatoMoneda(this.estadisticasBasicas.costo_total_acumulado)],
  //         ["Demanda Máxima Prom.", `${this.formatoNumero(this.estadisticasBasicas.demanda_maxima_promedio_kw)} kW`],
  //         ["Factor de Potencia", this.formatoPorcentaje(this.estadisticasBasicas.factor_potencia_promedio)],
  //         [],
  //         ["ANÁLISIS DE CORRELACIÓN", "COEFICIENTE"],
  //         ["Consumo vs Costo", this.estadisticasAnalisis.correlaciones.consumo_costo],
  //         ["Demanda vs Consumo", this.estadisticasAnalisis.correlaciones.demanda_consumo]
  //       ];
  //       const wsResumen = XLSX.utils.aoa_to_sheet(resumenData);
  //       // Ajustar ancho de columnas para que se vea bien
  //       wsResumen['!cols'] = [{wch: 30}, {wch: 20}];
  //       XLSX.utils.book_append_sheet(wb, wsResumen, "Resumen Ejecutivo");


  //       // =========================================================
  //       // HOJA 2: ESTADÍSTICAS ANUALES
  //       // Fuente: estadisticasAnalisis.estadisticas_anuales (Endpoint 2)
  //       // =========================================================
  //       if (this.estadisticasAnalisis.estadisticas_anuales.length > 0) {
  //           const datosAnuales = this.estadisticasAnalisis.estadisticas_anuales.map(item => ({
  //             "Año": item.año,
  //             "Consumo Total (kWh)": item.consumo_total_kwh_sum,
  //             "Consumo Promedio (kWh)": item.consumo_total_kwh_mean,
  //             "Costo Total (MXN)": item.costo_total_sum,
  //             "Costo Promedio (MXN)": item.costo_total_mean,
  //             "Demanda Máx (kW)": item.demanda_maxima_kw_max,
  //             "Demanda Prom (kW)": item.demanda_maxima_kw_mean
  //           }));
  //           const wsAnual = XLSX.utils.json_to_sheet(datosAnuales);
  //           wsAnual['!cols'] = [{wch:10}, {wch:20}, {wch:20}, {wch:18}, {wch:18}, {wch:18}, {wch:18}];
  //           XLSX.utils.book_append_sheet(wb, wsAnual, "Comparativa Anual");
  //       }


  //       // =========================================================
  //       // HOJA 3: PATRÓN MENSUAL PROMEDIO
  //       // Fuente: estadisticasAnalisis.patron_mensual (Endpoint 2)
  //       // =========================================================
  //       if (this.estadisticasAnalisis.patron_mensual.length > 0) {
  //           const datosPatron = this.estadisticasAnalisis.patron_mensual.map(item => ({
  //               "Mes": item.mes,
  //               "Consumo Promedio (kWh)": item.consumo_total_kwh,
  //               "Costo Promedio (MXN)": item.costo_total
  //           }));
  //           const wsPatron = XLSX.utils.json_to_sheet(datosPatron);
  //           wsPatron['!cols'] = [{wch:15}, {wch:25}, {wch:25}];
  //           XLSX.utils.book_append_sheet(wb, wsPatron, "Patrón Mensual");
  //       }


  //       // =========================================================
  //       // HOJA 4: HISTÓRICO COMPLETO (Evolución)
  //       // Fuente: tendenciasMensuales (Endpoint 1)
  //       // =========================================================
  //       if (this.tendenciasMensuales.length > 0) {
  //           const datosHistoricos = this.tendenciasMensuales.map(item => ({
  //             "Periodo": item.periodo, // Ej: 2021-01
  //             "Consumo (kWh)": item.consumo_total_kwh,
  //             "Costo (MXN)": item.costo_total,
  //             "Demanda Máx (kW)": item.demanda_maxima_kw,
  //             "Factor Potencia (%)": item.factor_potencia_promedio
  //           }));
  //           const wsHistorico = XLSX.utils.json_to_sheet(datosHistoricos);
  //           wsHistorico['!cols'] = [{wch:15}, {wch:20}, {wch:20}, {wch:20}, {wch:20}];
  //           XLSX.utils.book_append_sheet(wb, wsHistorico, "Histórico Completo");
  //       }

  //       // 4. Descargar el archivo
  //       const fecha = new Date().toISOString().slice(0,10);
  //       XLSX.writeFile(wb, `Analisis_Energetico_${fecha}.xlsx`);

  //     } catch (error) {
  //       console.error("Error al exportar:", error);
  //       alert("Hubo un error al generar el Excel. Revise la consola para más detalles.");
  //     }
  //   }
  }, // Cierre de methods
}; // Cierre de export default
</script>


<style scoped lang="scss">
@use "sass:color";

// ==========================================
// 1. MIXINS DE RESPONSIVIDAD (Utilidad)
// ==========================================
@mixin mobile {
    @media (max-width: 768px) { @content; }
}

@mixin tablet {
    @media (max-width: 992px) { @content; }
}

// ==========================================
// 2. LAYOUT PRINCIPAL
// ==========================================
.plataforma-layout {
    display: flex;
    min-height: 100vh;
    transition: background-color 0.3s ease;
    overflow-x: hidden;
    position: relative;
    width: 100%;
}

.plataforma-contenido {
    flex-grow: 1;
    // Padding fluido: reduce espacio en móviles automáticamente
    padding: clamp(15px, 3vw, 40px);
    transition: margin-left 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    margin-left: 80px; 
    width: 100%;
    
    &.shifted { margin-left: 280px; }

    // En tablet/móvil eliminamos el margen izquierdo para usar todo el ancho
    @include tablet {
        margin-left: 0 !important;
        width: 100%;
        &.shifted { margin-left: 0; }
    }
}

.resumen-estadistico-container {
    max-width: 100%; // Asegura que no desborde
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: clamp(20px, 2.5vw, 30px);
}

.dashboard-grid {
    display: flex;
    flex-direction: column;
    gap: clamp(20px, 3vw, 30px);
}

// ==========================================
// 3. KPI CARDS (Grid Fluido)
// ==========================================
.kpi-grid {
    display: grid;
    // Ajuste dinámico: reduce el mínimo a 220px para móviles pequeños
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
    gap: clamp(15px, 2vw, 20px);
}

.kpi-card {
    border-radius: 16px;
    padding: clamp(15px, 2vw, 20px);
    display: flex;
    align-items: center;
    gap: 15px;
    box-shadow: $shadow-soft;
    transition: all 0.3s ease;
    border: 1px solid transparent;
    position: relative;
    overflow: hidden;

    &:hover {
        transform: translateY(-4px);
        box-shadow: $shadow-strong;
        border-color: $PRIMARY-PURPLE;
    }

    .kpi-icon {
        // Tamaño adaptable
        width: clamp(40px, 4vw, 50px);
        height: clamp(40px, 4vw, 50px);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: clamp(1.2rem, 1.5vw, 1.5rem);
        flex-shrink: 0;
        background-color: rgba($PRIMARY-PURPLE, 0.1);
        color: $PRIMARY-PURPLE;
    }

    .kpi-content {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-width: 0; 
        flex: 1;

        .kpi-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: $GRAY-COLD;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 2px;
        }

        .kpi-value {
            font-size: clamp(1.1rem, 4vw, 1.4rem); 
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.2;
            
            small {
                font-size: 0.7em;
                font-weight: 500;
                opacity: 0.7;
                margin-left: 2px;
            }
        }
    }
}

.btn-export {
    background-color: $SUCCESS; 
    color: $WHITE;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s ease;
    box-shadow: $shadow-soft;
    // Ancho completo en móvil para mejor toque
    @include mobile {
        width: 100%;
        justify-content: center;
    }

    &:hover {
        background-color: color.adjust($SUCCESS, $lightness: -5%);
        transform: translateY(-2px);
        box-shadow: $shadow-strong;
    }

    i { font-size: 1.1rem; }
}

.actions-bar {
    margin-bottom: 20px;
    display: flex;
    justify-content: flex-end; // Alineación por defecto
    
    @include mobile {
        justify-content: stretch; // Estirar en móvil
    }
}

// ==========================================
// 4. GRÁFICOS (Grid Adaptable)
// ==========================================
.charts-row {
    display: grid;
    // Cambio crítico: minmax(100%, 1fr) permite que en pantallas pequeñas
    // el gráfico ocupe toda la fila. En grandes usa el espacio disponible.
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 500px), 1fr));
    gap: 25px;
}

.chart-container {
    border-radius: 16px;
    padding: clamp(15px, 2vw, 25px); // Padding reducido en móvil
    box-shadow: $shadow-soft;
    display: flex;
    flex-direction: column;
    min-height: 400px; // Altura base
    height: 100%;
    transition: box-shadow 0.3s ease;
    border: 1px solid transparent;

    @include mobile {
        min-height: 350px; // Altura ajustada para móvil
    }

    &:hover { box-shadow: $shadow-strong; }

    &.full-width {
        grid-column: 1 / -1; // Fuerza ancho completo
        min-height: 500px;
        @include mobile { min-height: 400px; }
    }

    .chart-header {
        margin-bottom: 20px;
        
        h5 {
            margin: 0;
            font-size: clamp(1rem, 1.2vw, 1.1rem);
            font-weight: 700;
            border-left: 4px solid $PRIMARY-PURPLE;
            padding-left: 12px;
            word-wrap: break-word; // Evita desbordamiento de texto largo
        }
        
        .chart-subtitle {
            display: block;
            margin-top: 4px;
            font-size: 0.85rem;
            color: $GRAY-COLD;
            padding-left: 16px;
        }
    }

    .chart-body {
        flex-grow: 1;
        width: 100%;
        position: relative;
        overflow: hidden;
        min-height: 250px; // Asegura visibilidad del canvas
    }
}

// ==========================================
// 5. TABLA DE DATOS (Scroll Horizontal)
// ==========================================
.table-container {
    border-radius: 16px;
    padding: clamp(15px, 2vw, 25px);
    box-shadow: $shadow-soft;
    border: 1px solid transparent;
    overflow: hidden; // Contiene elementos internos

    .table-header {
        margin-bottom: 20px;
        h5 { 
            font-weight: 700; 
            color: $PRIMARY-PURPLE; 
            margin: 0; 
            font-size: 1.1rem;
        }
    }

    .table-responsive-wrapper {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch; // Suavidad en iOS
        border-radius: 8px;
        padding-bottom: 10px; // Espacio para scrollbar
        
        &::-webkit-scrollbar { height: 6px; }
        &::-webkit-scrollbar-thumb { background-color: $GRAY-COLD; border-radius: 4px; opacity: 0.5; }
    }

    .custom-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        // Permite que la tabla mantenga su estructura
        min-width: 800px; 

        th, td {
            padding: 16px;
            text-align: left;
            border-bottom: 1px solid transparent;
            white-space: nowrap;
        }

        th {
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky; // Cabecera fija al hacer scroll vertical
            top: 0;
            z-index: 10;
        }

        td {
            font-size: 0.95rem;
        }
    }

    .table-footer {
        margin-top: 15px;
        font-size: 0.85rem;
        color: $GRAY-COLD;
        display: flex;
        flex-wrap: wrap; // Permite saltos de línea en móvil
        align-items: center;
        gap: 8px;
        i { color: $PRIMARY-PURPLE; }
    }
}

// ==========================================
// 6. ALERTAS Y LOADING
// ==========================================
.alert-box {
    padding: 15px 20px;
    border-radius: 10px;
    display: flex;
    align-items: flex-start; // Alineación superior para texto largo
    gap: 12px;
    font-weight: 500;
    margin-bottom: 20px;
    font-size: 0.95rem;

    &.error { 
        background-color: rgba($DANGER, 0.1); 
        color: $DANGER; 
        border: 1px solid rgba($DANGER, 0.2); 
    }
    
    &.warning { 
        background-color: rgba($WARNING, 0.1); 
        color: color.adjust($WARNING, $lightness: -10%); 
        border: 1px solid rgba($WARNING, 0.2); 
    }
    
    i { 
        font-size: 1.2rem; 
        margin-top: 2px; // Alineación visual
    }
}

.loading-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba($BLACK, 0.7);
    backdrop-filter: blur(5px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 9999;
    color: $WHITE;
    
    .loading-text { 
        margin-top: 20px; 
        font-weight: 500; 
        letter-spacing: 1px; 
        color: $LIGHT-TEXT; 
        text-align: center;
        padding: 0 20px;
    }
}

// ==========================================
// 7. TEMAS (MODO CLARO / OSCURO)
// ==========================================

// --- TEMA CLARO ---
.theme-light {
    background-color: $WHITE-SOFT;
    color: $DARK-TEXT;

    .kpi-card, .chart-container, .table-container {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
    }

    .kpi-value { color: $DARK-TEXT; }
    .chart-header h5 { color: $DARK-TEXT; }

    .custom-table {
        th { background-color: $WHITE-SOFT; color: $GRAY-COLD; border-bottom: 1px solid $LIGHT-BORDER; }
        td { border-bottom: 1px solid $LIGHT-BORDER; color: $DARK-TEXT; }
        tbody tr:hover { background-color: rgba($PRIMARY-PURPLE, 0.03); }
    }
}

// --- TEMA OSCURO ---
.theme-dark {
    background-color: $DARK-BG-CONTRAST;
    color: $LIGHT-TEXT;

    .kpi-card, .chart-container, .table-container {
        background-color: $SUBTLE-BG-DARK;
        border-color: $DARK-BORDER;
        box-shadow: $shadow-dark;
    }

    .kpi-value { color: $LIGHT-TEXT; }
    .chart-header h5 { color: $LIGHT-TEXT; }

    .custom-table {
        th { 
            background-color: rgba($BLACK, 0.2); 
            color: $WHITE; 
            border-bottom: 1px solid $DARK-BORDER; 
        }
        td { 
            border-bottom: 1px solid $DARK-BORDER; 
            color: $LIGHT-TEXT; 
        }
        tbody tr:hover { 
            background-color: color.adjust($SUBTLE-BG-DARK, $lightness: 5%); 
        }
    }
}
</style>