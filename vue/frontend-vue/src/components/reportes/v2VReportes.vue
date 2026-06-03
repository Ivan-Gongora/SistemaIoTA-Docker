<template>
  <div class="plataforma_layout" :class="{ 'theme_dark': isDark, 'theme_light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma_contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma 
        titulo="Reportes Históricos"
        subtitulo="Exploración temporal de telemetría IoT"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="reportes_wrapper">
        
        <div class="control_panel_compact glass_card shadow_lg">
          
          <div class="row g-3 align-items-end">
            <div class="col-xl-3 col-lg-4 col-md-6">
              <label class="label_bold">Proyecto</label>
              <div class="input_modern">
                <i class="bi bi-folder2-open icon_accent"></i>
                <select v-model="form.proyectoId" @change="cargarDispositivos" class="select_clean">
                  <option :value="null" disabled>{{ loadingProyectos ? 'Cargando...' : 'Selecciona proyecto' }}</option>
                  <option v-for="p in proyectos" :key="p.id" :value="p.id">{{ p.nombre }}</option>
                </select>
              </div>
            </div>

            <div class="col-xl-3 col-lg-4 col-md-6">
              <label class="label_bold">Dispositivo</label>
              <div class="input_modern">
                <i class="bi bi-cpu icon_accent"></i>
                <select v-model="form.dispositivoId" @change="cargarCamposYFechas" class="select_clean" :disabled="!form.proyectoId">
                  <option :value="null" disabled>{{ loadingDispositivos ? 'Cargando...' : 'Selecciona dispositivo' }}</option>
                  <option v-for="d in dispositivos" :key="d.id" :value="d.id">{{ d.nombre }}</option>
                </select>
              </div>
            </div>

            <div class="col-xl-4 col-lg-4 col-md-12">
              <label class="label_bold">Periodo de Análisis</label>
              <div class="d-flex gap-2">
                <div class="input_modern flex-grow-1">
                  <input type="date" v-model="form.fechaInicio" :min="fechaMinima" :max="form.fechaFin" class="select_clean" :disabled="!form.dispositivoId" title="Fecha Inicio">
                </div>
                <div class="input_modern flex-grow-1">
                  <input type="date" v-model="form.fechaFin" :min="form.fechaInicio" :max="fechaMaxima" class="select_clean" :disabled="!form.dispositivoId" title="Fecha Fin">
                </div>
              </div>
            </div>

            <div class="col-xl-2 col-lg-12 col-md-12">
              <button @click="aplicarFiltros" class="btn_ejecutar w-100" :disabled="!listoParaConsultar">
                <i class="bi bi-search me-2"></i> Extraer Datos
              </button>
            </div>
          </div>

          <div class="row g-3 mt-1 align-items-center config_row">
            
            <div class="col-auto">
              <div class="toggle_modern">
                <span class="small fw-bold me-2 text_muted">VISTA:</span>
                <button class="btn_toggle" :class="{ 'activo': form.modoVista === 'multiple' }" @click="form.modoVista = 'multiple'">Múltiple</button>
                <button class="btn_toggle" :class="{ 'activo': form.modoVista === 'combinado' }" @click="form.modoVista = 'combinado'">Combinado</button>
              </div>
            </div>

            <div class="col-auto">
              <div class="toggle_modern">
                <span class="small fw-bold me-2 text_muted">CARGA:</span>
                <button class="btn_toggle optimizado" :class="{ 'activo': form.metodoCarga === 'optimizado' }" @click="form.metodoCarga = 'optimizado'">
                  <i class="bi bi-lightning-charge-fill me-1"></i> Optimizado
                </button>
                <button class="btn_toggle puro" :class="{ 'activo': form.metodoCarga === 'puro' }" @click="form.metodoCarga = 'puro'">
                  <i class="bi bi-database-fill-exclamation me-1"></i> Puro (Raw)
                </button>
              </div>
            </div>

            <div class="col-auto ms-auto d-flex gap-3">
              <label class="switch_wrapper" title="Activa líneas de límite en las gráficas">
                <span class="small fw-bold text_muted me-2">LÍMITES ASHRAE</span>
                <div class="switch">
                  <input type="checkbox" v-model="form.activarAnalisis" :disabled="!form.dispositivoId">
                  <span class="slider round"></span>
                </div>
              </label>
            </div>

          </div>

        </div>

        <div class="selector_metricas glass_card shadow_lg" v-if="campos.length > 0">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="fw-bold m-0"><i class="bi bi-check2-square text_accent me-2"></i>Métricas Disponibles</h5>
            <span class="small text_muted">Selecciona las variables a graficar</span>
          </div>

          <div v-if="loadingCampos" class="text-center p-3">
            <div class="spinner-border text-primary" role="status"></div>
          </div>

          <div class="metricas_grid" v-else>
            <div 
              v-for="c in campos" 
              :key="c.id" 
              class="tarjeta_metrica"
              :class="{ 'activa': form.camposIds.includes(c.id) }"
              @click="toggleCampo(c.id)"
            >
              <div class="icono_metrica"><i :class="getIcon(c.nombre)"></i></div>
              <div class="info_metrica">
                <span class="nombre">{{ c.nombre }}</span>
                <span class="unidad">{{ c.unidad?.simbolo || c.simbolo_unidad || 'N/A' }}</span>
              </div>
              <div class="check_indicador"><i class="bi bi-check-circle-fill"></i></div>
            </div>
          </div>
        </div>

        <div v-if="errorMsg" class="alert_box error mt-3 shadow_lg">
          <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
        </div>

        <div class="zona_graficas mt-4" v-if="filtrosAplicados.listos">
          
          <div class="charts_grid_multiple" v-if="filtrosAplicados.modoVista === 'multiple'">
            
            <GraficoTemperatura
              v-if="tieneTemperatura"
              :campos="obtenerObjetosCamposFiltrados('temperatura')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :limites="limitesFijos"
            />

            <GraficoHumedad
              v-if="tieneHumedad"
              :campos="obtenerObjetosCamposFiltrados('humedad')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :limites="limitesFijos"
            />

            <GraficoElectrico
              v-if="tieneElectrico"
              :campos="obtenerObjetosCamposFiltrados('potencia', 'corriente')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
            />

            <GraficoEnergia
              v-if="tieneEnergia"
              :campos="obtenerObjetosCamposFiltrados('energia', 'kwh')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
            />

            <GraficoIluminacion
              v-if="tieneIluminacion"
              :campos="obtenerObjetosCamposFiltrados('iluminacion', 'luz')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
            />

            <GraficoMovimiento
              v-if="tieneMovimiento"
              :campos="obtenerObjetosCamposFiltrados('movimiento', 'presencia')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
            />

            <GraficoHistorico
              v-for="campoId in camposGenericos"
              :key="`hist-${filtrosAplicados.dispositivoId}-${campoId}-${filtrosAplicados.rangoInicio}`"
              :campo-id="campoId"
              :titulo="obtenerNombreCampo(campoId)"
              :fecha-inicio="filtrosAplicados.rangoInicio" 
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
              :incluir-analisis="filtrosAplicados.activarAnalisis"
              :limites-personalizados="limitesFijos"
            />
          </div>
          
          <div class="charts_grid_single" v-else>
            <GraficoCombinado
              :key="`comb-${filtrosAplicados.dispositivoId}-${filtrosAplicados.rangoInicio}`"
              :campos="obtenerObjetosCampos(filtrosAplicados.camposIds)"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
            />
          </div>

        </div>

        <div v-if="!filtrosAplicados.listos && !loadingProyectos" class="empty_state glass_card mt-4 text-center py-5">
          <i class="bi bi-bar-chart-steps text_muted" style="font-size: 3rem;"></i>
          <h5 class="fw-bold mt-3">Panel en Espera</h5>
          <p class="text_muted">Configura el dispositivo, las fechas y presiona "Extraer Datos" para comenzar.</p>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
import GraficoCombinado from './GraficoCombinado.vue';
import GraficoTemperatura from './GraficoTemperatura.vue';
import GraficoHumedad from './GraficoHumedad.vue';
import GraficoElectrico from './GraficoElectrico.vue';
import GraficoEnergia from './GraficoEnergia.vue';
import GraficoIluminacion from './GraficoIluminacion.vue';
import GraficoMovimiento from './GraficoMovimiento.vue';
import GraficoHistorico from './GraficoHistorico.vue';

export default {
  name: 'VistaReportesHistoricos',
  components: {
    BarraLateralPlataforma,
    EncabezadoPlataforma,
    GraficoCombinado,
    GraficoTemperatura,
    GraficoHumedad,
    GraficoElectrico,
    GraficoEnergia,
    GraficoIluminacion,
    GraficoMovimiento,
    GraficoHistorico
  },
  data() {
    return {
      isDark: true,
      isSidebarOpen: true,
      
      proyectos: [],
      dispositivos: [],
      campos: [],
      
      loadingProyectos: true,
      loadingDispositivos: false,
      loadingCampos: false,
      errorMsg: null,
      
      fechaMinima: null,
      fechaMaxima: null,

      form: {
        proyectoId: null,
        dispositivoId: null,
        fechaInicio: '',
        fechaFin: '',
        horaInicio: '00:00',
        horaFin: '23:59',
        camposIds: [],
        modoVista: 'multiple',
        metodoCarga: 'optimizado',
        activarAnalisis: false
      },

      filtrosAplicados: {
        listos: false,
        dispositivoId: null,
        camposIds: [],
        rangoInicio: '',
        rangoFin: '',
        modoVista: 'multiple',
        metodoCarga: 'optimizado',
        activarAnalisis: false
      },

      limitesFijos: {
        tempMin: 20,
        tempMax: 26,
        humMin: 30,
        humMax: 65
      }
    };
  },
  computed: {
    tieneTemperatura() {
      return this.verificarSeleccion('temperatura');
    },
    tieneHumedad() {
      return this.verificarSeleccion('humedad');
    },
    tieneElectrico() {
      return this.verificarSeleccion('potencia', 'corriente');
    },
    tieneEnergia() {
      return this.verificarSeleccion('energia', 'kwh');
    },
    tieneIluminacion() {
      return this.verificarSeleccion('iluminacion', 'luz');
    },
    tieneMovimiento() {
      return this.verificarSeleccion('movimiento', 'presencia');
    },
    camposGenericos() {
      return this.filtrosAplicados.camposIds.filter(id => {
        const nombre = this.obtenerNombreCampo(id).toLowerCase();
        const esTermo = nombre.includes('temperatura') || nombre.includes('humedad');
        const esElec = nombre.includes('potencia') || nombre.includes('corriente');
        const esEne = nombre.includes('energia') || nombre.includes('kwh');
        const esIlu = nombre.includes('iluminacion') || nombre.includes('luz');
        const esMov = nombre.includes('movimiento') || nombre.includes('presencia');
        return !esTermo && !esElec && !esEne && !esIlu && !esMov;
      });
    },
    listoParaConsultar() {
      return this.form.dispositivoId && 
             this.form.fechaInicio && 
             this.form.fechaFin && 
             this.form.camposIds.length > 0;
    },
    baseUrlAPI() {
      return typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8001';
    }
  },
  watch: {
    'form.metodoCarga'(nuevoModo) {
      if (nuevoModo === 'puro' && this.form.camposIds.length > 2) {
        this.form.camposIds = this.form.camposIds.slice(0, 2);
        this.errorMsg = "Redujimos la selección a 2 variables para proteger el rendimiento del navegador en modo Puro.";
        setTimeout(() => { this.errorMsg = null; }, 5000);
      }
    }
  },
  mounted() {
    this.detectarTema();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleTheme);
    }
    this.cargarProyectos();
  },
  beforeUnmount() {
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleTheme);
    }
  },
  methods: {
    detectarTema() {
      this.isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    },
    handleTheme(e) {
      this.isDark = e.matches;
    },
    toggleSidebar() {
      this.isSidebarOpen = !this.isSidebarOpen;
    },
    getIcon(tipo) {
      if (!tipo) return 'bi bi-activity';
      const t = tipo.toLowerCase();
      if (t.includes('temperatura')) return 'bi bi-thermometer-half';
      if (t.includes('humedad')) return 'bi bi-droplet-half';
      if (t.includes('potencia') || t.includes('energia') || t.includes('kwh')) return 'bi bi-lightning-charge-fill';
      if (t.includes('corriente')) return 'bi bi-plug-fill';
      if (t.includes('luz') || t.includes('iluminacion')) return 'bi bi-brightness-high-fill';
      if (t.includes('movimiento')) return 'bi bi-person-walking';
      return 'bi bi-graph-up';
    },
    toggleCampo(id) {
      const idx = this.form.camposIds.indexOf(id);
      if (idx === -1) {
        if (this.form.metodoCarga === 'puro' && this.form.camposIds.length >= 2) {
          this.errorMsg = "En modo Puro solo puedes graficar 2 variables simultáneas.";
          setTimeout(() => { this.errorMsg = null; }, 3000);
          return;
        }
        this.form.camposIds.push(id);
      } else {
        this.form.camposIds.splice(idx, 1);
      }
    },
    obtenerNombreCampo(id) {
      const c = this.campos.find(x => x.id === id);
      return c ? c.nombre : 'Variable Desconocida';
    },
    obtenerObjetosCampos(ids) {
      return this.campos.filter(c => ids.includes(c.id));
    },
    verificarSeleccion(...palabrasClave) {
      return this.filtrosAplicados.camposIds.some(id => {
        const nombre = this.obtenerNombreCampo(id).toLowerCase();
        return palabrasClave.some(p => nombre.includes(p));
      });
    },
    obtenerObjetosCamposFiltrados(...palabrasClave) {
      const idsValidos = this.filtrosAplicados.camposIds.filter(id => {
        const nombre = this.obtenerNombreCampo(id).toLowerCase();
        return palabrasClave.some(p => nombre.includes(p));
      });
      return this.obtenerObjetosCampos(idsValidos);
    },

    async cargarProyectos() {
      this.loadingProyectos = true;
      const token = localStorage.getItem('accessToken');
      const resultadoLocal = JSON.parse(localStorage.getItem('resultado') || '{}');
      const usuarioId = resultadoLocal.usuario?.id;

      if (!token || !usuarioId) return; 

      try {
        const response = await fetch(`${this.baseUrlAPI}/api/proyectos/usuario/${usuarioId}?page=1&limit=100`, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (response.ok) {
          const res = await response.json();
          this.proyectos = res.data || [];
          if (this.proyectos.length > 0) {
            this.form.proyectoId = this.proyectos[0].id;
            await this.cargarDispositivos(); 
          }
        }
      } catch (err) {
        this.errorMsg = "Fallo de red al obtener proyectos.";
      } finally {
        this.loadingProyectos = false;
      }
    },

    async cargarDispositivos() {
      this.loadingDispositivos = true;
      this.dispositivos = []; 
      this.form.dispositivoId = null;
      this.limpiarFormularioCampos();
      this.filtrosAplicados.listos = false;
      
      const token = localStorage.getItem('accessToken');
      if (!this.form.proyectoId) return;

      try {
        const response = await fetch(`${this.baseUrlAPI}/api/dispositivos/proyecto/${this.form.proyectoId}?page=1&limit=100`, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (response.ok) { 
          const res = await response.json();
          this.dispositivos = res.data || [];
          if (this.dispositivos.length > 0) {
            this.form.dispositivoId = this.dispositivos[0].id;
            await this.cargarCamposYFechas();
          }
        }
      } catch (err) {
        this.errorMsg = "Fallo al cargar la lista de dispositivos.";
      } finally {
        this.loadingDispositivos = false;
      }
    },

    async cargarCamposYFechas() {
      this.limpiarFormularioCampos();
      this.filtrosAplicados.listos = false;
      await this.cargarCampos();
      await this.cargarRangoDeFechas();
    },

    limpiarFormularioCampos() {
      this.campos = [];
      this.form.camposIds = [];
      this.fechaMinima = null;
      this.fechaMaxima = null;
      this.form.fechaInicio = '';
      this.form.fechaFin = '';
    },

    async cargarCampos() {
      this.loadingCampos = true;
      this.errorMsg = null;
      
      const token = localStorage.getItem('accessToken');
      if (!this.form.dispositivoId) return;

      try {
        const sensoresResponse = await fetch(`${this.baseUrlAPI}/api/sensores/dispositivo/${this.form.dispositivoId}?page=1&limit=50`, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        let sensores = [];
        if (sensoresResponse.ok) {
          const res = await sensoresResponse.json();
          sensores = Array.isArray(res) ? res : (res.data || []);
        }

        let todosLosCampos = [];
        for (const sensor of sensores) {
          const camposResponse = await fetch(`${this.baseUrlAPI}/api/sensores/${sensor.id}/campos`, { 
            headers: { 'Authorization': `Bearer ${token}` } 
          });
          
          if (camposResponse.ok) {
            const res = await camposResponse.json();
            const listaCampos = res.campos || (Array.isArray(res) ? res : []);
            todosLosCampos.push(...listaCampos); 
          }
        }
        this.campos = todosLosCampos; 
        
        if (this.campos.length > 0) {
            this.form.camposIds = this.campos.map(c => c.id);
        }

      } catch (err) {
        this.errorMsg = 'Error en el servidor al cargar las variables técnicas.';
      } finally {
        this.loadingCampos = false;
      }
    },

    async cargarRangoDeFechas() {
      const token = localStorage.getItem('accessToken');
      if (!this.form.dispositivoId) return;

      try {
        const response = await fetch(`${this.baseUrlAPI}/api/valores/rango-fechas-dispositivo/${this.form.dispositivoId}`, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (response.ok) {
          const rango = await response.json(); 
          if (rango.fecha_minima && rango.fecha_maxima) {
            this.fechaMinima = rango.fecha_minima.split('T')[0];
            this.fechaMaxima = rango.fecha_maxima.split('T')[0];
            
            const maxDate = new Date(rango.fecha_maxima);
            const sevenDaysAgo = new Date(maxDate);
            sevenDaysAgo.setDate(maxDate.getDate() - 7);
            
            const minDateObj = new Date(rango.fecha_minima);
            const startStr = (sevenDaysAgo > minDateObj ? sevenDaysAgo : minDateObj).toISOString().split('T')[0];
            
            this.form.fechaInicio = startStr;
            this.form.fechaFin = this.fechaMaxima;
            return;
          }
        }
        this.asignarFechasLocales();
      } catch (err) {
        this.asignarFechasLocales();
      }
    },

    asignarFechasLocales() {
      const hoyStr = new Date().toISOString().split('T')[0];
      this.form.fechaInicio = hoyStr;
      this.form.fechaFin = hoyStr;
    },

    aplicarFiltros() {
      this.filtrosAplicados.dispositivoId = this.form.dispositivoId;
      this.filtrosAplicados.camposIds = [...this.form.camposIds];
      this.filtrosAplicados.rangoInicio = `${this.form.fechaInicio}T${this.form.horaInicio}:00`;
      this.filtrosAplicados.rangoFin = `${this.form.fechaFin}T${this.form.horaFin}:00`;
      this.filtrosAplicados.modoVista = this.form.modoVista;
      this.filtrosAplicados.metodoCarga = this.form.metodoCarga;
      this.filtrosAplicados.activarAnalisis = this.form.activarAnalisis;
      this.filtrosAplicados.listos = true;
    }
  }
};
</script>

<style scoped lang="scss">
.plataforma_layout { display: flex; width: 100%; min-height: 100vh; transition: background-color 0.3s; }
.theme_light { background-color: $WHITE-SOFT; color: $DARK-TEXT; }
.theme_dark { background-color: $DARK-BG-CONTRAST; color: $LIGHT-TEXT; }

.plataforma_contenido { flex-grow: 1; padding: 30px; margin-left: $WIDTH-CLOSED; transition: margin-left 0.3s; }
.shifted { margin-left: $WIDTH-SIDEBAR; }
.reportes_wrapper { max-width: 1600px; margin: 0 auto; }

.glass_card { border-radius: $border-radius-lg; padding: 24px; margin-bottom: 24px; transition: background-color 0.3s, border-color 0.3s; }
.theme_light .glass_card { background: $LIGHT-BG-CARD; border: 1px solid $LIGHT-BORDER; box-shadow: $shadow-soft; }
.theme_dark .glass_card { background: $BG-CARD-DARK; border: 1px solid $DARK-BORDER; box-shadow: $shadow-dark; }

.control_panel_compact { padding: 20px 24px; }
.label_bold { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; display: block; }
.theme_light .label_bold { color: $GRAY-COLD; }
.theme_dark .label_bold { color: $GRAY-LIGHT; }

.input_modern { display: flex; align-items: center; padding: 12px 16px; border-radius: 12px; gap: 12px; transition: background-color 0.2s, box-shadow 0.2s; }
.theme_light .input_modern { background: $LIGHT-INPUT-BG; border: 1px solid $LIGHT-BORDER; }
.theme_dark .input_modern { background: $DARK-INPUT-BG; border: 1px solid $DARK-BORDER; }
.input_modern:focus-within { box-shadow: 0 0 0 2px rgba(138, 43, 226, 0.4); border-color: $PRIMARY-PURPLE; }

.icon_accent { color: $PRIMARY-PURPLE; font-size: 1.1rem; }

.select_clean { border: none; background: transparent; width: 100%; font-weight: 600; outline: none; font-size: 0.95rem; }
.theme_light .select_clean { color: $DARK-TEXT; }
.theme_dark .select_clean { color: $LIGHT-TEXT; }
.theme_dark .select_clean option { background: $BG-CARD-DARK; color: $LIGHT-TEXT; }

.btn_ejecutar { background: $PRIMARY-PURPLE; color: $WHITE; border: none; padding: 14px 24px; border-radius: 12px; font-weight: 800; cursor: pointer; transition: transform 0.2s, filter 0.2s, background 0.2s; height: 48px; }
.btn_ejecutar:disabled { background: $INACTIVE-COLOR; cursor: not-allowed; opacity: 0.6; }
.btn_ejecutar:not(:disabled):hover { transform: translateY(-2px); filter: brightness(1.1); box-shadow: $shadow-purple; }

.config_row { border-top: 1px solid; padding-top: 16px; margin-top: 16px; }
.theme_light .config_row { border-color: $LIGHT-BORDER; }
.theme_dark .config_row { border-color: $DARK-BORDER; }

.toggle_modern { display: flex; align-items: center; background: transparent; border-radius: 10px; padding: 4px; border: 1px solid; }
.theme_light .toggle_modern { border-color: $LIGHT-BORDER; }
.theme_dark .toggle_modern { border-color: $DARK-BORDER; }

.btn_toggle { background: transparent; border: none; padding: 6px 14px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; cursor: pointer; transition: all 0.2s; color: inherit; }
.theme_light .btn_toggle { color: $GRAY-COLD; }
.theme_dark .btn_toggle { color: $GRAY-LIGHT; }
.btn_toggle.activo { background: $PRIMARY-PURPLE; color: $WHITE; }
.btn_toggle.optimizado.activo { background: $SUCCESS-COLOR; }
.btn_toggle.puro.activo { background: $WARNING-COLOR; color: $DARK-TEXT; }

.text_muted { color: $GRAY-COLD; }
.text_accent { color: $PRIMARY-PURPLE; }

.metricas_grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }

.tarjeta_metrica { display: flex; align-items: center; padding: 12px 16px; border-radius: 12px; cursor: pointer; border: 1px solid transparent; transition: all 0.2s; position: relative; overflow: hidden; }
.theme_light .tarjeta_metrica { background: $SUBTLE-BG-LIGHT; border-color: $LIGHT-BORDER; }
.theme_dark .tarjeta_metrica { background: $SUBTLE-BG-DARK; border-color: $DARK-BORDER; }
.tarjeta_metrica:hover { border-color: $PRIMARY-PURPLE; transform: translateY(-2px); }
.tarjeta_metrica.activa { background: rgba(138, 43, 226, 0.1) !important; border-color: $PRIMARY-PURPLE !important; }

.icono_metrica { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-right: 12px; transition: color 0.2s; }
.theme_light .icono_metrica { background: rgba(0,0,0,0.05); color: $GRAY-COLD; }
.theme_dark .icono_metrica { background: rgba(255,255,255,0.05); color: $GRAY-LIGHT; }
.tarjeta_metrica.activa .icono_metrica { color: $PRIMARY-PURPLE; }

.info_metrica { display: flex; flex-direction: column; flex-grow: 1; }
.info_metrica .nombre { font-weight: 700; font-size: 0.9rem; }
.theme_light .info_metrica .nombre { color: $DARK-TEXT; }
.theme_dark .info_metrica .nombre { color: $LIGHT-TEXT; }
.info_metrica .unidad { font-size: 0.75rem; color: $GRAY-COLD; }

.check_indicador { position: absolute; top: 8px; right: 12px; color: $PRIMARY-PURPLE; opacity: 0; transform: scale(0.5); transition: all 0.2s; }
.tarjeta_metrica.activa .check_indicador { opacity: 1; transform: scale(1); }

.switch_wrapper { display: flex; align-items: center; cursor: pointer; }
.switch { position: relative; display: inline-block; width: 44px; height: 24px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: $INACTIVE-COLOR; transition: .3s; border-radius: 34px; }
.slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: $WHITE; transition: .3s; border-radius: 50%; }
input:checked + .slider { background-color: $PRIMARY-PURPLE; }
input:disabled + .slider { opacity: 0.5; cursor: not-allowed; }
input:checked + .slider:before { transform: translateX(20px); }

.charts_grid_multiple { display: grid; gap: 24px; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); }
.charts_grid_single { display: grid; grid-template-columns: 1fr; }

.alert_box { padding: 16px 20px; border-radius: 12px; font-weight: 600; }
.alert_box.error { background: rgba(231, 76, 60, 0.1); color: $DANGER-COLOR; border: 1px solid rgba(231, 76, 60, 0.3); }

@media (max-width: 768px) {
  .plataforma_contenido { margin-left: 0; padding: 15px; }
  .charts_grid_multiple { grid-template-columns: 1fr; }
  .config_row { flex-direction: column; align-items: stretch; }
  .config_row > div { width: 100%; margin-bottom: 10px; }
}
</style>