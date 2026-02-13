<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma
        titulo="Simulador Energético"
        subtitulo="Proyección de escenarios de consumo y costos energéticos institucionales."
        @toggle-sidebar="toggleSidebar"
        :is-sidebar-open="isSidebarOpen"
        :is-dark="isDark"
      />

      <div class="simulador-principal-contenido">

        <div v-if="lotesCargados && lotesCargados.length > 0" class="lotes-seleccionados-display">
          <i class="bi bi-stack"></i>
          <span class="lotes-titulo">Lotes en Simulación:</span>
          <span class="lotes-lista">{{ lotesCargados.join(', ') }}</span>
        </div>
        <div v-else class="lotes-seleccionados-display no-lotes">
            <i class="bi bi-info-circle-fill"></i> No se han seleccionado lotes de datos para simular.
            <router-link :to="{ name: 'MenuGestionDatosEnergeticos' }" class="boton-ir-gestion">
              Ir a Gestión de Datos
            </router-link>
        </div>

        <div class="simulador-grid">
          
          <div class="gestion-panel panel-controles">
            <h2 class="panel-titulo"><i class="bi bi-sliders"></i> Parámetros de Simulación</h2>

            <div class="control-grupo">
              <label for="meses">
                Horizontes (Meses): <span class="valor-resaltado">{{ meses }}</span>
              </label>
              <input type="range" id="meses" min="12" max="120" step="12" v-model.number="meses"/>
            </div>

            <div class="control-grupo">
              <label for="inflacion">
                Inflación Energética Anual: <span class="valor-resaltado">{{ formatPercent(simulacionParams.tasa_inflacion_energetica) }}</span>
              </label>
              <input type="range" id="inflacion" min="0" max="0.3" step="0.01" v-model.number="simulacionParams.tasa_inflacion_energetica"/>
            </div>

            <div class="control-grupo">
              <label for="crecimiento">
                Crecimiento Consumo Anual: <span class="valor-resaltado">{{ formatPercent(simulacionParams.tasa_crecimiento_consumo) }}</span>
              </label>
              <input type="range" id="crecimiento" min="-0.1" max="0.3" step="0.01" v-model.number="simulacionParams.tasa_crecimiento_consumo"/>
            </div>

            <div class="control-grupo">
              <label for="eficiencia">
                Reducción por Eficiencia: <span class="valor-resaltado">{{ formatPercent(simulacionParams.mejora_eficiencia_consumo) }}</span>
              </label>
              <input type="range" id="eficiencia" min="0" max="0.5" step="0.01" v-model.number="simulacionParams.mejora_eficiencia_consumo"/>
            </div>

            <button @click="ejecutarSimulacion" :disabled="isLoading || !lotesCargados || lotesCargados.length === 0" class="boton-simular">
              <i v-if="isLoading" class="bi bi-arrow-repeat spin"></i>
              <i v-else class="bi bi-play-circle-fill"></i>
              {{ isLoading ? 'Simulando...' : 'Ejecutar Simulación' }}
            </button>
          </div>

          <div class="columna-resultados">
            
            <div class="resumen-costos-grid">
              
              <div class="tarjeta-resumen tarjeta-base" 
                   title="Consumo total proyectado de energía si no se realizan cambios ni optimizaciones. Es el punto de referencia base.">
                <span class="titulo-resumen">Consumo Base ({{ meses }} m)</span>
                <p class="valor-grande">{{ formatKWH(simulacionResultado.total_consumo_base_kwh) }}</p>
              </div>

              <div class="tarjeta-resumen tarjeta-simulado" 
                   title="Consumo total proyectado de energía considerando el crecimiento y las mejoras de eficiencia que has configurado.">
                <span class="titulo-resumen">Consumo Simulado ({{ meses }} m)</span>
                <p class="valor-grande">{{ formatKWH(simulacionResultado.total_consumo_simulado_kwh) }}</p>
              </div>

              <div class="tarjeta-resumen tarjeta-variacion" 
                   :class="simulacionResultado.variacion_consumo_total_kwh <= 0 ? 'variacion-negativa' : 'variacion-positiva'"
                   title="Variación total de Consumo (kWh) estimada entre el escenario simulado y el escenario base.">
                <span class="titulo-resumen">Variación vs. Base (kWh)</span>
                <p class="valor-grande">
                    {{ formatKWH(simulacionResultado.variacion_consumo_total_kwh) }}
                </p>
                <span class="leyenda-variacion">
                    ({{ simulacionResultado.variacion_consumo_total_kwh <= 0 ? 'Reducción' : 'Aumento' }})
                </span>
              </div>
            </div>
            
            <div class="grafica-simulador-contenedor">
              <h3 class="panel-titulo">
                  Proyección de Consumo (kWh): Histórico y Simulado
                    <i class="bi bi-info-circle-fill info-icon"
                      data-bs-toggle="popover"
                      data-bs-trigger="hover focus"
                      data-bs-html="true"
                      data-bs-placement="top"
                      :data-bs-title="popoverTitle"
                      :data-bs-content="popoverContent">
                    </i>
              </h3>
              
              <GraficoSimulacionECharts
                v-if="fullChartData && fullChartData.datos_historicos_usados && fullChartData.predicciones_escenario"
                :chart-data="fullChartData"
                :is-dark="isDark"
              />
              <div v-else class="mensaje-placeholder">
                <i class="bi bi-bar-chart-fill"></i> 
                {{ isLoading ? 'Calculando proyección...' : 'Ajuste los parámetros y haga clic en "Ejecutar Simulación".' }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="errorApi" class="alerta alerta-error mt-4">
          <i class="bi bi-exclamation-octagon-fill"></i>
          <strong>Error:</strong> {{ errorApi }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
import GraficoSimulacionECharts from '../graficos/GraficoSimulacionECharts.vue';
import * as bootstrap from 'bootstrap';

// Asume que 'bootstrap' y 'API_BASE_URL' están disponibles globalmente.

export default {
  name: 'VistaSimuladorEnergetico',
  components: {
    BarraLateralPlataforma,
    EncabezadoPlataforma,
    GraficoSimulacionECharts,
  },
  data() {
    return {
      isDark: false,
      isSidebarOpen: true,
      
      lotesCargados: [], 
      
      meses: 24, 
      simulacionParams: {
        tasa_inflacion_energetica: 0.08,
        tasa_crecimiento_consumo: 0.05,
        mejora_eficiencia_consumo: 0.10
      },
      isLoading: false,
      simulacionResultado: { 
        // KPIs de Costo (para el resumen detallado o futuro uso)
        total_meses_simulados: 0,
        total_costo_base_mxn: 0,
        total_costo_simulado_mxn: 0,
        variacion_costo_total_mxn: 0,
        porcentaje_variacion: 0,
        // KPIs de Consumo (usados en el template)
        total_consumo_base_kwh: 0,
        total_consumo_simulado_kwh: 0,
        variacion_consumo_total_kwh: 0,
        
        parametros_escenario: {},
        lotes_simulados: [],
      },
      fullChartData: null, 
      errorApi: null,
      
      _themeMediaQuery: null,
      popoverTitle: "Análisis de Proyección de Consumo",
      popoverContent: `
        <p>Esta gráfica ilustra la evolución mensual de tu consumo energético (kWh) en un horizonte de tiempo.</p>
        <p>La línea <strong>Consumo Base</strong> (línea discontinua) muestra el consumo histórico **real** y su proyección futura sin aplicar mejoras.</p>
        <p>La línea <strong>Consumo Simulado</strong> (línea sólida) muestra el consumo esperado aplicando la reducción por eficiencia configurada.</p>
        <p>Una diferencia visible a la baja en la línea simulada respecto a la base indica una reducción efectiva del consumo proyectado.</p>
      `
    };
  },
  mounted() {
    this.initPopovers();
    this.detectarTemaSistema(); 
    this.cargarLotesDesdeUrl(); 
    if (window.matchMedia) {
      this._themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      this._themeMediaQuery.addEventListener('change', this.handleThemeChange); 
    }
  },
  beforeUnmount() {
    if (this._themeMediaQuery) {
      this._themeMediaQuery.removeEventListener('change', this.handleThemeChange);
    }
  },
  methods: {
    // --- Métodos de Layout y Carga Inicial ---
    initPopovers() {
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        
        // El operador spread ([...]) y map funcionan bien para inicializar Bootstrap Popovers
        [...popoverTriggerList].map(popoverTriggerEl => {
            if (bootstrap.Popover.getInstance(popoverTriggerEl)) {
                bootstrap.Popover.getInstance(popoverTriggerEl).dispose();
            }
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },
    toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; },
    
    // Método para manejar el cambio de tema del sistema
    handleThemeChange(event) { 
      this.isDark = event.matches; 
      // Forzar actualización de la gráfica si hay datos
      if(this.fullChartData) {
          this.fullChartData = { ...this.fullChartData };
      }
    },
    
    // Método para detectar el tema inicial
    detectarTemaSistema() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) { 
          this.isDark = true; 
        } else { 
          this.isDark = false; 
        }
    },
    
    // Método para cargar lotes desde la URL (query parameter)
    cargarLotesDesdeUrl() {
      const lotesQuery = this.$route.query.lotes;
      if (lotesQuery) {
        // Asegura que lotesCargados sea un array
        this.lotesCargados = Array.isArray(lotesQuery) ? lotesQuery : [lotesQuery];
      } else {
        this.lotesCargados = []; 
      }
    },
    
    // --- Métodos de Formato ---
    formatPercent(value) { return (value * 100).toFixed(1) + '%'; },
    formatCurrency(value) { 
        if (value === null || value === undefined) return '$0';
        const absValue = Math.abs(value);
        return `${value < 0 ? '-' : ''}${absValue.toLocaleString('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 0 })}`;
    },
    // Formato para kWh
    formatKWH(value) {
        if (value === null || value === undefined) return '0 kWh';
        const absValue = Math.abs(value);
        const formatted = absValue.toLocaleString('es-MX', { maximumFractionDigits: 0 });
        return `${value < 0 ? '-' : ''}${formatted} kWh`;
    },
    
    // --- Lógica de Simulación ---
    async ejecutarSimulacion() {
      if (!this.lotesCargados || this.lotesCargados.length === 0) {
        this.errorApi = "Seleccione al menos un lote de datos para simular.";
        return;
      }
      
      this.isLoading = true;
      this.errorApi = null;
      this.fullChartData = null; 

      const token = localStorage.getItem('accessToken');
      if (!token) { this.errorApi = "Error de autenticación. Inicia sesión."; this.isLoading = false; this.$router.push('/'); return; }

      const API_URL = `${API_BASE_URL}/api/energetico/simular/escenario_personalizado`; 
      
      try {
        const payload = {
          tasa_inflacion_energetica: this.simulacionParams.tasa_inflacion_energetica,
          tasa_crecimiento_consumo: this.simulacionParams.tasa_crecimiento_consumo,
          mejora_eficiencia_consumo: this.simulacionParams.mejora_eficiencia_consumo,
          lotes_seleccionados: this.lotesCargados,
          meses_a_predecir: this.meses
        };

        const response = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        const resultado = await response.json();

        if (!response.ok || resultado.status !== 'success') {
          const detail = resultado.detail || resultado.error || "Fallo en el servicio de simulación.";
          throw new Error(detail);
        }
        
        const data = resultado.data;

        // --- CÁLCULO DE CONSUMOS TOTALES ---
        const historico = data.datos_historicos_usados || [];
        const proyeccion = data.predicciones_escenario || [];
        
        const totalConsumoReal = historico.reduce((sum, item) => sum + item.consumo_total_kwh, 0);
        const totalConsumoBaseProyectado = proyeccion.reduce((sum, item) => sum + item.consumo_base_kwh, 0);
        const totalConsumoSimuladoProyectado = proyeccion.reduce((sum, item) => sum + item.consumo_escenario_kwh, 0);
        
        const totalBase = totalConsumoReal + totalConsumoBaseProyectado;
        const totalSimulado = totalConsumoReal + totalConsumoSimuladoProyectado; 

        // 1. Actualizar Resumen KPI
        this.simulacionResultado = {
            ...data.resumen_simulacion,
            total_costo_base_mxn: data.resumen_simulacion.total_costo_base_mxn,
            total_costo_simulado_mxn: data.resumen_simulacion.total_costo_simulado_mxn,
            variacion_costo_total_mxn: data.resumen_simulacion.variacion_costo_total_mxn,
            
            total_consumo_base_kwh: totalBase,
            total_consumo_simulado_kwh: totalSimulado,
            variacion_consumo_total_kwh: totalSimulado - totalBase,
        }; 

        // 2. Asignar el objeto 'data' completo al prop de la gráfica
        this.fullChartData = data;

      } catch (error) {
        console.error("Error en la simulación:", error);
        this.errorApi = error.message || "Error al conectar con la API de simulación.";
      } finally {
        this.isLoading = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
@use "sass:color";

/* -----------------------------------------------------------------
 * VARIABLES Y THEME SETUP
 * ----------------------------------------------------------------- */

.plataforma-layout {
  display: flex;
  min-height: 100vh;
  transition: background-color 0.3s ease; 
  background-color: $WHITE-SOFT; 

  &.theme-dark {
    --card-bg: #{$SUBTLE-BG-DARK};
    --card-border: #{$DARK-BORDER};
    --text-color-primary: #{$LIGHT-TEXT};
    --text-color-secondary: #{$GRAY-COLD};
    --color-heading: #{$LIGHT-TEXT}; 
    --input-bg: #{$DARK-INPUT-BG}; 
    background-color: $DARK-BG-CONTRAST; 
  }

  &.theme-light {
    --card-bg: #{$SUBTLE-BG-LIGHT};
    --card-border: #{$LIGHT-BORDER};
    --text-color-primary: #{$DARK-TEXT};
    --text-color-secondary: #{$GRAY-COLD};
    --color-heading: #{$DARK-TEXT}; 
    --input-bg: #{$LIGHT-INPUT-BG}; 
    background-color: $WHITE-SOFT; 
  }
}

.simulador-principal-contenido {
    // MEJORA: Padding fluido. 1rem en móviles, 2rem en desktop.
    padding: clamp(1rem, 3vw, 2rem);
    width: 100%;
    max-width: 1800px; // Aumentado ligeramente para monitores ultrawide
    margin: 0 auto;
}

/* ------------------------------------
 * LAYOUT GRID PRINCIPAL (INTELIGENTE)
 * ------------------------------------ */

.simulador-grid {
  display: grid;
  // MEJORA: La columna lateral es flexible entre 300px y 350px.
  // El contenido principal toma el resto (1fr).
  grid-template-columns: minmax(300px, 350px) 1fr;
  gap: 1.5rem; 
  margin-top: 1.5rem;
  align-items: start; // Importante para que el sticky funcione
}

/* ------------------------------------
 * DISPLAY DE LOTES
 * ------------------------------------ */
.lotes-seleccionados-display {
  display: flex;
  justify-content: space-between; // Maximiza el espacio horizontal
  align-items: center;
  gap: 1rem;
  background-color: var(--card-bg); 
  border: 1px solid var(--card-border); 
  border-radius: $border-radius;
  padding: 0.75rem 1.25rem; // Padding más compacto
  box-shadow: $box-shadow-sm;
  color: var(--text-color-primary); 
  font-size: 1rem;
  margin-bottom: 1rem; 
  flex-wrap: wrap; // Permite que caiga en móviles sin romper

  &.no-lotes {
      background-color: rgba($WARNING-COLOR, 0.1);
      border-color: $WARNING-COLOR;
      color: $WARNING-COLOR;
  }

  .info-grupo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  i {
    color: $PRIMARY-PURPLE;
    font-size: 1.3rem;
  }
  
  .lotes-titulo { font-weight: 600; white-space: nowrap; }
  .lotes-lista { 
    font-weight: 400; 
    color: var(--text-color-secondary);
    // Trunca el texto si es muy largo en móviles
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 50vw; 
  }
}

.boton-ir-gestion {
    background-color: $PRIMARY-PURPLE;
    color: $WHITE;
    padding: 0.4rem 0.9rem; // Botón más compacto
    border-radius: $border-radius-sm;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background-color 0.2s ease;
    white-space: nowrap;

    &:hover {
        background-color: color.adjust($PRIMARY-PURPLE, $lightness: -5%);
    }
}

/* ------------------------------------
 * PANELES DE CONTROL (SIDEBAR)
 * ------------------------------------ */
.gestion-panel {
  background-color: var(--card-bg); 
  border: 1px solid var(--card-border); 
  border-radius: $border-radius;
  box-shadow: $box-shadow-sm;
  padding: 1.25rem; // Reducido ligeramente para ganar espacio interno
  
  // MEJORA: Sticky para aprovechar el espacio vertical en scroll
  position: sticky;
  top: 1.5rem; 
  z-index: 10;
  max-height: calc(100vh - 3rem); // Evita que se corte si es muy alto
  overflow-y: auto; // Scroll interno si la pantalla es bajita
}

.panel-controles .panel-titulo {
  color: var(--text-color-primary); 
  font-size: 1.1rem; // Tamaño de fuente optimizado
  font-weight: 700;
  border-bottom: 1px solid var(--card-border); 
  padding-bottom: 0.75rem;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  i { color: $PRIMARY-PURPLE; font-size: 1.2rem; }
}

.control-grupo {
  margin-bottom: 1.25rem; // Espaciado más compacto
  
  label {
    display: flex; 
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    margin-bottom: 0.4rem;
    color: var(--text-color-primary); 
    font-size: 0.9rem;
  }

  input[type="range"] {
    width: 100%;
    height: 6px; // Slider más fino y elegante
    background: var(--input-bg); 
    border-radius: 4px;
    outline: none;
    transition: background 0.2s ease-in-out;
    cursor: pointer;
    
    &::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: $PRIMARY-PURPLE;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
      margin-top: -5px; // Centrar verticalmente si es necesario
    }
    // ... estilos firefox thumb (mismos ajustes)
  }
}

.valor-resaltado {
  font-weight: 700;
  color: $PRIMARY-PURPLE;
  background: rgba($PRIMARY-PURPLE, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85rem;
}

.boton-simular {
  width: 100%;
  padding: 0.75rem;
  font-weight: 600;
  color: white;
  background-image: $PURPLE-GRADIENT; 
  border-radius: $border-radius-sm;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem; 
  font-size: 1rem;
  margin-top: 1rem;

  &:hover:not(:disabled) {
    box-shadow: 0 4px 12px rgba($PRIMARY-PURPLE, 0.3);
    transform: translateY(-2px); 
  }
  &:disabled {
    background-image: none; 
    background-color: var(--input-bg);
    color: var(--text-color-secondary);
    cursor: not-allowed;
    box-shadow: none;
  }
}

/* ------------------------------------
 * RESULTADOS Y GRÁFICA (ZONA DERECHA)
 * ------------------------------------ */
.columna-resultados {
  display: flex;
  flex-direction: column;
  gap: 1.5rem; // Gap consistente
  min-width: 0; // CRÍTICO: Evita que la gráfica rompa el grid flex
}

// MEJORA: Grid de tarjetas auto-ajustable
.resumen-costos-grid {
  display: grid;
  // Intenta meter 3 columnas, pero si baja de cierto ancho, hace wrap
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem; 
}

.tarjeta-resumen {
  background-color: var(--card-bg); 
  border: 1px solid var(--card-border); 
  border-radius: $border-radius;
  padding: 1rem; 
  box-shadow: $box-shadow-sm;
  display: flex;
  flex-direction: column;
  justify-content: center;

  .titulo-resumen {
    font-size: 0.85rem;
    color: var(--text-color-secondary); 
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.25rem;
  }

  .valor-grande {
    font-size: clamp(1.5rem, 2vw, 2rem); // Texto fluido
    font-weight: 800;
    color: var(--color-heading); 
  }

  .leyenda-variacion {
    font-size: 0.8rem;
    color: var(--text-color-secondary); 
    margin-top: auto; // Empuja hacia abajo si hay espacio extra
  }

  // Variaciones de color
  &.tarjeta-variacion {
    &.variacion-negativa { 
      background: linear-gradient(to right, rgba($SUCCESS-COLOR, 0.1), transparent);
      border-left: 4px solid $SUCCESS-COLOR;
      .valor-grande { color: $SUCCESS-COLOR; }
    }
    &.variacion-positiva { 
      background: linear-gradient(to right, rgba($DANGER-COLOR, 0.1), transparent);
      border-left: 4px solid $DANGER-COLOR;
      .valor-grande { color: $DANGER-COLOR; }
    }
  }
}

.grafica-simulador-contenedor {
  background-color: var(--card-bg); 
  border: 1px solid var(--card-border); 
  border-radius: $border-radius;
  box-shadow: $box-shadow-sm;
  padding: 1.25rem;
  flex-grow: 1; // Ocupa el espacio vertical restante
  display: flex;
  flex-direction: column;

  .panel-titulo {
      margin-bottom: 0.75rem;
      font-size: 1.1rem;
      color: var(--text-color-primary); 
  }
  
  // Asegura que el canvas del gráfico tenga espacio
  .chart-wrapper {
      flex-grow: 1;
      min-height: 400px; // Altura mínima garantizada
      position: relative;
  }
}

/* ------------------------------------
 * RESPONSIVE AVANZADO
 * ------------------------------------ */

// Tablet vertical y Laptops pequeñas (menos de 1024px)
@media (max-width: 1024px) {
  .simulador-grid {
    // Cambiamos a layout vertical antes para dar espacio a la gráfica en tablets
    grid-template-columns: 1fr; 
    gap: 1.5rem;
  }
  
  .gestion-panel {
    position: static; // Quitamos sticky porque ahora está arriba
    max-height: none;
    
    // Convertimos los controles en un grid de 2 columnas para aprovechar el ancho
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
    
    .panel-titulo { grid-column: 1 / -1; margin-bottom: 0.5rem; }
    .boton-simular { grid-column: 1 / -1; width: 50%; margin-left: auto; }
  }
  
  .columna-resultados {
      order: 2; // Resultados debajo de controles si se prefiere, o ajustar orden HTML
  }
}

// Móviles (menos de 768px)
@media (max-width: 768px) {
    .simulador-principal-contenido {
        padding: 1rem; // Menos padding en contenedor general
    }

    .gestion-panel {
        display: block; // Volvemos a bloque simple (1 columna)
        padding: 1rem;
        
        .boton-simular { width: 100%; }
    }

    .resumen-costos-grid {
        // Forzamos 1 columna en móviles muy estrechos, o mantenemos auto-fit
        grid-template-columns: 1fr;
    }

    .tarjeta-resumen {
        flex-direction: row; // En móvil, quizás se ve mejor horizontal: Titulo - Valor
        justify-content: space-between;
        align-items: center;
        
        .leyenda-variacion { display: none; } // Ocultamos detalles finos para ahorrar espacio
    }
    
    .grafica-simulador-contenedor {
        padding: 0.75rem;
        .chart-wrapper { min-height: 300px; }
    }
}
</style>