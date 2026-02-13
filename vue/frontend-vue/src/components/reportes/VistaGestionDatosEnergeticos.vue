<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">

    <BarraLateralPlataforma :is-open="isSidebarOpen" />

    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">

      <EncabezadoPlataforma
        titulo="Gestión de Datos Energéticos"
        subtitulo="Carga y selecciona tus conjuntos de datos de consumo eléctrico (lotes) para analizarlos."
        @toggle-sidebar="toggleSidebar"
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="gestion-datos-contenido">
        
        <div class="gestion-grid">
          
          <!-- PANEL IZQUIERDO: CARGA -->
          <div class="gestion-panel">
            <h2 class="panel-titulo">
              <i class="bi bi-cloud-upload-fill"></i>
              Cargar Lote de Datos (CSV)
            </h2>

            <!-- Feedback de Carga -->
            <div v-if="mensajeCarga" :class="['mensaje-carga', tipoMensajeCarga === 'success' ? 'mensaje-exito' : 'mensaje-error']">
              <i :class="tipoMensajeCarga === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
              {{ mensajeCarga }}
            </div>

            <div class="campo-lote-nombre">
              <label for="loteNombreInput">Nombre del Lote:</label>
              <div class="input-con-icono">
                <i class="bi bi-tag-fill"></i>
                <input
                  type="text"
                  id="loteNombreInput"
                  v-model="inputLoteNombre"
                  placeholder="Ej. Recibos Casa 2023"
                  class="input-lote"
                  :class="{'input-error': loteNombreVacio && !inputLoteNombre.trim()}"
                />
              </div>
              <p v-if="loteNombreVacio && !inputLoteNombre.trim()" class="error-texto">Por favor, ingresa un nombre para el lote.</p>
            </div>
            
            <label for="csvFile" class="boton-seleccionar-archivo">
              <i class="bi bi-file-earmark-spreadsheet-fill"></i>
              <span>{{ nombreArchivo || 'Seleccionar archivo CSV...' }}</span>
            </label>
            <input
              type="file"
              id="csvFile"
              ref="csvFileInput"
              @change="handleFileChange"
              accept=".csv"
              hidden
            />

            <p class="ayuda-texto-formato">
              Columnas requeridas: periodo, consumo_total_kwh, demanda_maxima_kw, costo_total, dias_facturados.
            </p>
            
            <!-- 🚨 NUEVO: SECCIÓN DE DESCARGAS (PLANTILLAS) -->
            <div class="recursos-ayuda">
                <p class="titulo-ayuda"><i class="bi bi-info-circle"></i> ¿Necesitas ayuda con el formato?</p>
                <div class="botones-descarga">
                    <a href="/documents/GuiaCrearCsvRecibos.txt" download="Guia_Formato_CSV.txt" class="btn-link-ayuda">
                        <i class="bi bi-file-text"></i> Descargar Guía TXT
                    </a>
                    <a href="/documents/recibos.csv" download="Plantilla_Recibos.csv" class="btn-link-ayuda">
                        <i class="bi bi-file-earmark-excel"></i> Descargar Plantilla CSV
                    </a>
                </div>
            </div>

            <button @click="subirCSV" :disabled="!archivoSeleccionado || isLoadingCarga || !inputLoteNombre.trim()" class="boton-cargar">
              <i class="bi bi-arrow-up-circle-fill"></i>
              {{ isLoadingCarga ? 'Cargando...' : 'Cargar y Procesar Datos' }}
            </button>
          </div>

          <!-- PANEL DERECHO: SELECCIÓN -->
          <div class="columna-derecha">
            
            <div class="gestion-panel seleccion-lotes-panel">
              <h2 class="panel-titulo">
                <i class="bi bi-check-square-fill"></i>
                Seleccionar Datos para Análisis
              </h2>

              <div v-if="isLoadingLotes" class="cargando-lotes">
                <div class="spinner"></div> Cargando lotes...
              </div>
              <div v-else-if="lotesDisponibles.length === 0" class="no-lotes">
                <i class="bi bi-info-circle-fill"></i> No tienes lotes de datos cargados.
              </div>
              
              <div v-else class="lista-lotes">
                <p class="ayuda-texto">Selecciona uno o más lotes para habilitar las herramientas:</p>
                
                <div
                  v-for="loteNombre in lotesDisponibles"
                  :key="loteNombre"
                  class="checkbox-lote"
                  @click="toggleLote(loteNombre)"
                  :class="{ 'seleccionado': lotesSeleccionados.includes(loteNombre) }"
                >
                  <i :class="lotesSeleccionados.includes(loteNombre) ? 'bi bi-check-circle-fill' : 'bi bi-circle'"></i>
                  
                  <label :for="`lote-${loteNombre}`">{{ loteNombre }}</label>
                  
                  <input
                    type="checkbox"
                    :value="loteNombre"
                    v-model="lotesSeleccionados"
                    :id="`lote-${loteNombre}`"
                    hidden
                  />
                </div>
              </div>
              <div v-if="lotesError" class="mensaje-error">
                Error al cargar lotes: {{ lotesError }}
              </div>
            </div>

            <div class="gestion-panel herramientas-panel">
              <h2 class="panel-titulo">
                <i class="bi bi-tools"></i>
                Herramientas de Análisis
              </h2>
              
              <div v-if="lotesSeleccionados.length > 0" class="ayuda-texto-estado estado-ok">
                <i class="bi bi-check-circle-fill"></i>
                Lotes seleccionados. ¡Listo para analizar!
              </div>
              <div v-else class="ayuda-texto-estado estado-warn">
                 <i class="bi bi-exclamation-triangle-fill"></i>
                Selecciona al menos un lote de datos.
              </div>

              <div class="botones-herramientas">
                <router-link :to="{ name: 'VistaSimuladorEnergetico', query: { lotes: lotesSeleccionados } }" custom v-slot="{ navigate }">
                  <button @click="navigate" :disabled="!lotesSeleccionados.length" class="boton-herramienta boton-primario">
                    <i class="bi bi-graph-up"></i>
                    Ir a Simulación de Escenario
                  </button>
                </router-link>

                <router-link :to="{ name: 'VistaResumenEstadistico', query: { lotes: lotesSeleccionados } }" custom v-slot="{ navigate }">
                  <button @click="navigate" :disabled="!lotesSeleccionados.length" class="boton-herramienta boton-secundario">
                    <i class="bi bi-clipboard-data-fill"></i>
                    Ver Análisis Descriptivo
                  </button>
                </router-link>
              </div>
            </div>
          </div> 
        </div> 
      </div> 
    </div>
  </div>
</template>

<script>
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';


export default {
  name: 'VistaGestionDatosEnergeticos',
  components: {
    BarraLateralPlataforma,
    EncabezadoPlataforma,
  },
  data() {
    return {
      isDark: false,
      isSidebarOpen: true,
      _themeMediaQuery: null,

      archivoSeleccionado: null,
      nombreArchivo: '',
      isLoadingCarga: false,
      mensajeCarga: '',
      tipoMensajeCarga: '', 
      inputLoteNombre: '',
      loteNombreVacio: false,

      lotesDisponibles: [], 
      lotesSeleccionados: [], 
      isLoadingLotes: false,
      lotesError: null,
    };
  },
  mounted() {
    this.detectarTemaSistema();
    this._themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    if (this._themeMediaQuery) {
      this._themeMediaQuery.addEventListener('change', this.handleThemeChange);
    }
    this.obtenerLotesUsuario();
  },
  unmounted() {
    if (this._themeMediaQuery) {
      this._themeMediaQuery.removeEventListener('change', this.handleThemeChange);
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
    
    handleFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.archivoSeleccionado = file;
        this.nombreArchivo = file.name;
        this.mensajeCarga = ''; 
        this.tipoMensajeCarga = '';
      } else {
        this.archivoSeleccionado = null;
        this.nombreArchivo = '';
      }
    },

    async subirCSV() {
      if (!this.inputLoteNombre.trim()) {
        this.mensajeCarga = "Por favor, ingresa un nombre para el conjunto de datos.";
        this.tipoMensajeCarga = 'error';
        this.loteNombreVacio = true;
        return;
      } else { this.loteNombreVacio = false; }

      if (!this.archivoSeleccionado) {
        this.mensajeCarga = "Por favor, selecciona un archivo CSV.";
        this.tipoMensajeCarga = 'error';
        return;
      }

      this.isLoadingCarga = true;
      this.mensajeCarga = '';
      this.tipoMensajeCarga = '';

      const token = localStorage.getItem('accessToken');
      if (!token) {
        this.mensajeCarga = "Error de autenticación. Inicia sesión.";
        this.tipoMensajeCarga = 'error';
        this.isLoadingCarga = false;
        this.$router.push('/');
        return;
      }

      const formData = new FormData();
      formData.append('file', this.archivoSeleccionado);
      formData.append('lote_nombre', this.inputLoteNombre.trim());

      try {
        const response = await fetch(`${API_BASE_URL}/api/energetico/cargar-csv`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData
        });

        const resultado = await response.json();

        if (response.ok) {
          this.mensajeCarga = resultado.message || "Datos cargados exitosamente.";
          this.tipoMensajeCarga = 'success';
          await this.obtenerLotesUsuario(); 
          this.archivoSeleccionado = null;
          this.nombreArchivo = '';
          this.inputLoteNombre = '';
          if (this.$refs.csvFileInput) { this.$refs.csvFileInput.value = null; }
        } else {
           if (response.status === 409) {
               this.mensajeCarga = resultado.detail || "Error: Ya existen datos para algunos periodos en el lote especificado.";
           } else if (response.status === 401 || response.status === 403) {
               localStorage.removeItem('accessToken'); this.$router.push('/');
               throw new Error("Token inválido o expirado.");
           } else {
               this.mensajeCarga = resultado.detail || `Error ${response.status} al cargar el archivo.`;
           }
           this.tipoMensajeCarga = 'error';
        }
      } catch (error) {
        console.error("Error al subir CSV:", error);
         if (!this.mensajeCarga) { this.mensajeCarga = error.message || "Error de red o conexión al subir el archivo."; }
        this.tipoMensajeCarga = 'error';
      } finally {
        this.isLoadingCarga = false;
      }
    },

    async obtenerLotesUsuario() {
      this.isLoadingLotes = true;
      this.lotesDisponibles = [];
      this.lotesError = null;

      const token = localStorage.getItem('accessToken');
      if (!token) { this.lotesError = "No autenticado."; this.isLoadingLotes = false; return; }

      try {
        const response = await fetch(`${API_BASE_URL}/api/energetico/lotes_disponibles`, {
          method: 'GET',
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json(); 
          this.lotesDisponibles = data; 
          this.cargarSeleccionLotesDesdeLocalStorage();
        } else if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('accessToken'); this.$router.push('/'); this.lotesError = "Sesión expirada.";
        } else {
          const errorData = await response.json();
          this.lotesError = errorData.detail || `Error ${response.status} al obtener los lotes.`;
        }
      } catch (error) {
        console.error("Error de red al obtener lotes:", error);
        this.lotesError = "Error de conexión o red al obtener lotes.";
      } finally {
        this.isLoadingLotes = false;
      }
    },

    toggleLote(loteNombre) { 
      const index = this.lotesSeleccionados.indexOf(loteNombre);
      if (index > -1) {
        this.lotesSeleccionados.splice(index, 1); 
      } else {
        this.lotesSeleccionados.push(loteNombre); 
      }
    },

    guardarSeleccionLotes() {
      localStorage.setItem('selectedEnergyDataLotes', JSON.stringify(this.lotesSeleccionados));
    },

    cargarSeleccionLotesDesdeLocalStorage() {
      const storedLotes = localStorage.getItem('selectedEnergyDataLotes');
      if (storedLotes) {
        const parsedLotes = JSON.parse(storedLotes);
        this.lotesSeleccionados = parsedLotes.filter(lote => 
          this.lotesDisponibles.includes(lote)
        );
      }
    }
  },
  watch: {
    lotesSeleccionados: {
      handler() { this.guardarSeleccionLotes(); },
      deep: true
    },
    lotesDisponibles: {
      handler() { this.cargarSeleccionLotesDesdeLocalStorage(); },
      immediate: true
    }
  }
};
</script>

<style scoped lang="scss">
@use "sass:color";

// =============================================================================
// 1. LAYOUT PRINCIPAL
// =============================================================================
.gestion-datos-contenido {
    padding: 30px 40px;
    max-width: 1600px;
    margin: 0 auto;
    animation: fadeIn 0.4s ease-out;

    @media (max-width: 768px) {
        padding: 20px;
    }
}

.gestion-grid {
    display: grid;
    grid-template-columns: 1fr 1fr; // Dos columnas por defecto
    gap: 30px;

    @media (max-width: 1024px) {
        grid-template-columns: 1fr; // Una columna en tablets/móviles
    }
}

// -----------------------------------
// 2. PANELES (TARJETAS)
// -----------------------------------
.gestion-panel {
    border-radius: 16px;
    padding: 30px;
    box-shadow: $shadow-soft; // Variable Global
    display: flex;
    flex-direction: column;
    gap: 25px;
    transition: all 0.3s ease;
    border: 1px solid transparent; // Preparado para hover/temas
}

.panel-titulo {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: $PRIMARY-PURPLE;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    
    i { font-size: 1.2rem; }
}

// -----------------------------------
// 3. FORMULARIOS E INPUTS
// -----------------------------------
.campo-lote-nombre {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    label {
        font-weight: 600;
        font-size: 0.9rem;
        color: $GRAY-COLD;
    }
}

.input-con-icono {
    position: relative;
    
    i {
        position: absolute;
        left: 14px;
        top: 50%;
        transform: translateY(-50%);
        color: $GRAY-COLD;
        font-size: 1rem;
        transition: color 0.3s;
    }
    
    .input-lote {
        width: 100%;
        padding: 12px 12px 12px 40px;
        border-radius: 10px;
        border: 1px solid transparent; // Color definido en temas
        font-size: 0.95rem;
        transition: all 0.3s ease;
        
        &:focus {
            border-color: $PRIMARY-PURPLE !important;
            box-shadow: 0 0 0 4px rgba($PRIMARY-PURPLE, 0.1);
            outline: none;
            
            & + i { color: $PRIMARY-PURPLE; } // Ilumina el icono al enfocar
        }
        
        &.input-error {
            border-color: $DANGER !important;
            box-shadow: 0 0 0 4px rgba($DANGER, 0.1);
        }
    }
}

.error-texto {
    color: $DANGER;
    font-size: 0.8rem;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 5px;
    font-weight: 500;
}

// -----------------------------------
// 4. UPLOAD DE ARCHIVOS (DRAG & DROP STYLE)
// -----------------------------------
.boton-seleccionar-archivo {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 30px;
    border: 2px dashed $GRAY-LIGHT; // Borde suave por defecto
    border-radius: 12px;
    cursor: pointer;
    color: $GRAY-COLD;
    background-color: rgba($GRAY-COLD, 0.03);
    transition: all 0.3s ease;
    text-align: center;
    
    i { font-size: 2rem; margin-bottom: 5px; opacity: 0.7; }
    span { font-size: 0.9rem; font-weight: 500; }

    &:hover {
        border-color: $PRIMARY-PURPLE;
        color: $PRIMARY-PURPLE;
        background-color: rgba($PRIMARY-PURPLE, 0.05);
        transform: translateY(-2px);
    }
}

// -----------------------------------
// 5. RECURSOS DE AYUDA (BOX)
// -----------------------------------
.recursos-ayuda {
    margin-top: 10px;
    padding: 20px;
    background-color: rgba($PRIMARY-PURPLE, 0.04);
    border-radius: 12px;
    border: 1px solid rgba($PRIMARY-PURPLE, 0.1);
    
    .titulo-ayuda {
        font-size: 0.85rem;
        font-weight: 700;
        color: $PRIMARY-PURPLE;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .botones-descarga {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        
        .btn-link-ayuda {
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            color: $GRAY-COLD; // Color base
            background-color: transparent;
            padding: 8px 16px;
            border-radius: 20px;
            border: 1px solid; // Color en temas
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            
            &:hover {
                border-color: $PRIMARY-PURPLE;
                color: $PRIMARY-PURPLE;
                background-color: $WHITE;
                box-shadow: 0 4px 10px rgba($PRIMARY-PURPLE, 0.15);
                transform: translateY(-2px);
            }
        }
    }
}

// -----------------------------------
// 6. BOTONES DE ACCIÓN (GRADIENTES)
// -----------------------------------
.boton-cargar {
    width: 100%;
    margin-top: 15px;
    background: linear-gradient(135deg, $PRIMARY-PURPLE, color.adjust($PRIMARY-PURPLE, $lightness: -10%));
    color: $WHITE;
    border: none;
    padding: 14px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    box-shadow: 0 4px 15px rgba($PRIMARY-PURPLE, 0.3);
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba($PRIMARY-PURPLE, 0.4);
    }
    
    &:disabled {
        background: $GRAY-LIGHT;
        color: $GRAY-COLD;
        box-shadow: none;
        cursor: not-allowed;
    }
}

// -----------------------------------
// 7. LISTA DE LOTES (SELECCIÓN)
// -----------------------------------
.lista-lotes {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 400px; // Más espacio vertical
    overflow-y: auto;
    padding-right: 5px; // Espacio para scrollbar

    // Custom Scrollbar
    &::-webkit-scrollbar { width: 6px; }
    &::-webkit-scrollbar-thumb { background-color: $GRAY-LIGHT; border-radius: 3px; }

    .checkbox-lote {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 15px;
        border: 1px solid transparent; // Definido en temas
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
        
        // Icono de estado (círculo vacío o check)
        i { 
            font-size: 1.3rem; 
            color: $GRAY-COLD; 
            transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        label { 
            cursor: pointer; 
            font-weight: 500; 
            flex: 1; 
            white-space: nowrap; 
            overflow: hidden; 
            text-overflow: ellipsis; 
        }
        
        // Estado Seleccionado
        &.seleccionado {
            border-color: $SUCCESS;
            background-color: rgba($SUCCESS, 0.08);
            
            i { 
                color: $SUCCESS; 
                transform: scale(1.1);
            }
            label { color: $SUCCESS; font-weight: 700; }
        }
        
        &:hover:not(.seleccionado) {
            transform: translateX(5px);
        }
    }
}

// -----------------------------------
// 8. HERRAMIENTAS (BOTONES LATERALES)
// -----------------------------------
.botones-herramientas {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-top: auto; // Empuja hacia abajo si hay espacio

    .boton-herramienta {
        width: 100%;
        padding: 16px;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        font-size: 1rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        transition: all 0.3s ease;
        
        &.boton-primario {
            background: linear-gradient(135deg, $SUCCESS, color.adjust($SUCCESS, $lightness: -10%));
            color: $WHITE;
            box-shadow: 0 4px 15px rgba($SUCCESS, 0.3);
            
            &:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba($SUCCESS, 0.4);
            }
        }
        
        &.boton-secundario {
            background-color: transparent;
            border: 2px solid $PRIMARY-PURPLE;
            color: $PRIMARY-PURPLE;
            
            &:hover:not(:disabled) {
                background-color: rgba($PRIMARY-PURPLE, 0.05);
                transform: translateY(-2px);
            }
        }
        
        &:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            filter: grayscale(100%);
            box-shadow: none;
        }
    }
}

// =============================================================================
// 9. TEMAS (CLARO / OSCURO)
// =============================================================================

// --- TEMA CLARO ---
.theme-light {
    background-color: $WHITE-SOFT;

    .gestion-panel {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
    }

    .input-lote {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
        color: $DARK-TEXT;
    }

    .checkbox-lote {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
        label { color: $DARK-TEXT; }
        &:hover:not(.seleccionado) { background-color: $WHITE-SOFT; }
    }

    .recursos-ayuda .botones-descarga .btn-link-ayuda {
        border-color: $LIGHT-BORDER;
        background-color: $WHITE;
    }
}

// --- TEMA OSCURO ---
.theme-dark {
    background-color: $DARK-BG-CONTRAST; // Fondo general
    color: $LIGHT-TEXT;

    .gestion-panel {
        background-color: $SUBTLE-BG-DARK; // Tarjeta
        border-color: rgba($WHITE, 0.05);
    }

    .input-lote {
        background-color: $DARK-INPUT-BG;
        border-color: $DARK-BORDER;
        color: $WHITE;
    }

    .boton-seleccionar-archivo {
        border-color: $DARK-BORDER;
        &:hover { border-color: $PRIMARY-PURPLE; background-color: rgba($PRIMARY-PURPLE, 0.1); }
    }

    .checkbox-lote {
        background-color: $SUBTLE-BG-DARK;
        border-color: $DARK-BORDER;
        label { color: $GRAY-LIGHT; } // Texto legible
        
        &:hover:not(.seleccionado) { 
            background-color: color.adjust($SUBTLE-BG-DARK, $lightness: 5%); 
        }
    }

    .recursos-ayuda .botones-descarga .btn-link-ayuda {
        background-color: $DARK-INPUT-BG;
        border-color: $DARK-BORDER;
        color: $GRAY-LIGHT;
        
        &:hover { 
            border-color: $PRIMARY-PURPLE; 
            color: $PRIMARY-PURPLE; 
            background-color: color.adjust($DARK-INPUT-BG, $lightness: 5%);
        }
    }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>