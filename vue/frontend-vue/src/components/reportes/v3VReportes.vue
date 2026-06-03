<template>
  <div class="plataforma_layout" :class="{ 'theme_dark': isDark, 'theme_light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma_contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <!-- ENCABEZADO SUPERIOR -->
      <div class="header_dashboard">
        <div class="header_titles">
          <h2 class="main_title">Historial de Telemetría</h2>
          <span class="sub_title">Monitoreo de datos IoT</span>
        </div>
        
        <div class="header_selectors">
          <div class="input_compact">
            <i class="bi bi-folder2-open icon_purple"></i>
            <select v-model="form.proyectoId" @change="cargarDispositivos" class="select_invisible">
              <option :value="null" disabled>{{ loadingProyectos ? 'Cargando...' : 'Proyecto' }}</option>
              <option v-for="p in proyectos" :key="p.id" :value="p.id">{{ p.nombre }}</option>
            </select>
          </div>
          <div class="input_compact">
            <i class="bi bi-cpu icon_purple"></i>
            <select v-model="form.dispositivoId" @change="cargarCamposYFechas" class="select_invisible" :disabled="!form.proyectoId">
              <option :value="null" disabled>{{ loadingDispositivos ? 'Cargando...' : 'Dispositivo' }}</option>
              <option v-for="d in dispositivos" :key="d.id" :value="d.id">{{ d.nombre }}</option>
            </select>
          </div>
        </div>
      </div>

      <div class="reportes_wrapper">
        
        <!-- BARRA DE CONFIGURACIÓN Y MÉTRICAS -->
        <div class="config_toolbar shadow_soft">
          
          <div class="toolbar_top">
            <div class="date_group">
              <div class="date_input">
                <i class="bi bi-calendar-event text_muted"></i>
                <input type="date" v-model="form.fechaInicio" :min="fechaMinima" :max="form.fechaFin" :disabled="!form.dispositivoId">
              </div>
              <span class="text_muted">hasta</span>
              <div class="date_input">
                <i class="bi bi-calendar-check text_muted"></i>
                <input type="date" v-model="form.fechaFin" :min="form.fechaInicio" :max="fechaMaxima" :disabled="!form.dispositivoId">
              </div>
            </div>

            <div class="view_toggles">
               <button class="pill_btn" :class="{ 'activo': form.modoVista === 'multiple' }" @click="form.modoVista = 'multiple'">Múltiple</button>
               <button class="pill_btn" :class="{ 'activo': form.modoVista === 'combinado' }" @click="form.modoVista = 'combinado'">Combinado</button>
               <div class="divider"></div>
               <button class="pill_btn optimizado" :class="{ 'activo': form.metodoCarga === 'optimizado' }" @click="form.metodoCarga = 'optimizado'">Optimizado</button>
               <button class="pill_btn puro" :class="{ 'activo': form.metodoCarga === 'puro' }" @click="form.metodoCarga = 'puro'">Raw</button>
            </div>

            <div class="action_group">
              <label class="switch_wrapper" title="Activa líneas de límite ASHRAE">
                <span class="fw_bold text_muted me-2">Análisis ASHRAE</span>
                <div class="switch">
                  <input type="checkbox" v-model="form.activarAnalisis" :disabled="!form.dispositivoId">
                  <span class="slider round"></span>
                </div>
              </label>

              <button @click="aplicarFiltros" class="btn_extract" :disabled="!listoParaConsultar">
                <i class="bi bi-cloud-arrow-down-fill me-2"></i> Extraer
              </button>
            </div>
          </div>

          <!-- PANEL DESPLEGABLE DE LÍMITES ASHRAE -->
          <div class="limits_panel" v-if="form.activarAnalisis">
            <span class="limits_title"><i class="bi bi-sliders"></i> Ajuste de Umbrales</span>
            <div class="limit_box">
              <label>Temp Mín (°C)</label>
              <input type="number" v-model.number="form.limites.tempMin" class="limit_input">
            </div>
            <div class="limit_box">
              <label>Temp Máx (°C)</label>
              <input type="number" v-model.number="form.limites.tempMax" class="limit_input">
            </div>
            <div class="limit_box">
              <label>Hum Mín (%)</label>
              <input type="number" v-model.number="form.limites.humMin" class="limit_input">
            </div>
            <div class="limit_box">
              <label>Hum Máx (%)</label>
              <input type="number" v-model.number="form.limites.humMax" class="limit_input">
            </div>
          </div>

          <!-- ETIQUETAS DE MÉTRICAS -->
          <div class="metrics_bar mt-3" v-if="campos.length > 0">
            <span class="fw_bold text_muted me-3 mt-1">Variables:</span>
            <div class="metrics_scroll">
              <div 
                v-for="c in campos" 
                :key="c.id" 
                class="metric_chip"
                :class="{ 'activo': form.camposIds.includes(c.id) }"
                @click="toggleCampo(c.id)"
              >
                <i :class="getIcon(c.nombre)"></i>
                <span class="m_name">{{ c.nombre }}</span>
                <span class="m_unit">{{ c.unidad?.simbolo || c.simbolo_unidad || '' }}</span>
              </div>
            </div>
          </div>

        </div>

        <div v-if="errorMsg" class="alert_box error shadow_soft">
          <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
        </div>

        <!-- ZONA DE GRÁFICAS -->
        <div class="dashboard_grid mt-4" v-if="filtrosAplicados.listos">
          
          <template v-if="filtrosAplicados.modoVista === 'multiple'">
            
            <div class="grid_item span_1" v-if="tieneTemperatura">
              <GraficoTemperatura
                :campos="obtenerObjetosCamposFiltrados('temperatura')"
                :fecha-inicio="filtrosAplicados.rangoInicio"
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
                :limites="filtrosAplicados.limites"
              />
            </div>

            <div class="grid_item span_1" v-if="tieneHumedad">
              <GraficoHumedad
                :campos="obtenerObjetosCamposFiltrados('humedad')"
                :fecha-inicio="filtrosAplicados.rangoInicio"
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
                :limites="filtrosAplicados.limites"
              />
            </div>

            <div class="grid_item span_2" v-if="tieneElectrico">
              <GraficoElectrico
                :campos="obtenerObjetosCamposFiltrados('potencia', 'corriente')"
                :fecha-inicio="filtrosAplicados.rangoInicio"
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
              />
            </div>

            <div class="grid_item span_1" v-if="tieneEnergia">
              <GraficoEnergia
                :campos="obtenerObjetosCamposFiltrados('energia', 'kwh')"
                :fecha-inicio="filtrosAplicados.rangoInicio"
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
              />
            </div>

            <div class="grid_item span_1" v-if="tieneIluminacion">
              <GraficoIluminacion
                :campos="obtenerObjetosCamposFiltrados('iluminacion', 'luz')"
                :fecha-inicio="filtrosAplicados.rangoInicio"
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
              />
            </div>

            <div class="grid_item span_2" v-if="tieneMovimiento">
              <GraficoMovimiento
                :campos="obtenerObjetosCamposFiltrados('movimiento', 'presencia')"
                :fecha-inicio="filtrosAplicados.rangoInicio"
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
              />
            </div>

            <!-- Gráfica Genérica -->
            <div class="grid_item span_1" v-for="campoId in camposGenericos" :key="`hist-${campoId}`">
              <GraficoHistorico
                :campo-id="campoId"
                :titulo="obtenerNombreCampo(campoId)"
                :fecha-inicio="filtrosAplicados.rangoInicio" 
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
                :metodo-carga="filtrosAplicados.metodoCarga"
                :incluir-analisis="filtrosAplicados.activarAnalisis"
                :limites-personalizados="filtrosAplicados.limites"
              />
            </div>
          </template>
          
          <template v-else>
            <div class="grid_item span_2">
              <GraficoCombinado
                :key="`comb-${filtrosAplicados.rangoInicio}`"
                :campos="obtenerObjetosCampos(filtrosAplicados.camposIds)"
                :fecha-inicio="filtrosAplicados.rangoInicio"
                :fecha-fin="filtrosAplicados.rangoFin"
                :is-dark="isDark"
                :metodo-carga="filtrosAplicados.metodoCarga"
              />
            </div>
          </template>

        </div>

        <div v-if="!filtrosAplicados.listos && !loadingProyectos" class="empty_state glass_panel mt-4 text-center py-5 shadow_soft">
          <div class="empty_icon"><i class="bi bi-layers-fill"></i></div>
          <h4 class="fw_bold mt-3 text_light">Panel de Telemetría</h4>
          <p class="text_muted">Configura el dispositivo, selecciona fechas y extrae los datos.</p>
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
        activarAnalisis: false,
        limites: {
          tempMin: 20,
          tempMax: 26,
          humMin: 30,
          humMax: 65
        }
      },

      filtrosAplicados: {
        listos: false,
        dispositivoId: null,
        camposIds: [],
        rangoInicio: '',
        rangoFin: '',
        modoVista: 'multiple',
        metodoCarga: 'optimizado',
        activarAnalisis: false,
        limites: {}
      }
    };
  },
  computed: {
    tieneTemperatura() { return this.verificarSeleccion('temperatura'); },
    tieneHumedad() { return this.verificarSeleccion('humedad'); },
    tieneElectrico() { return this.verificarSeleccion('potencia', 'corriente'); },
    tieneEnergia() { return this.verificarSeleccion('energia', 'kwh'); },
    tieneIluminacion() { return this.verificarSeleccion('iluminacion', 'luz'); },
    tieneMovimiento() { return this.verificarSeleccion('movimiento', 'presencia'); },
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
        this.errorMsg = "Limitamos la selección a 2 variables para proteger el rendimiento en modo Puro.";
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
          this.errorMsg = "Solo extraes 2 variables simultáneas en modo Raw.";
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
        this.errorMsg = "Problema de red al ubicar proyectos.";
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
        this.errorMsg = "Error al descargar equipos.";
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
        this.errorMsg = 'Fallo al descargar métricas del equipo.';
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
      this.filtrosAplicados.limites = { ...this.form.limites };
      this.filtrosAplicados.listos = true;
    }
  }
};
</script>

<style scoped>
.plataforma_layout { display: flex; width: 100%; min-height: 100vh; transition: background-color 0.3s; }
.theme_light { background-color: #F7F9FC; color: #333333; }
.theme_dark { background-color: #1E1E30; color: #E4E6EB; }

.plataforma_contenido { flex-grow: 1; padding: 30px; margin-left: 80px; transition: margin-left 0.3s; }
.shifted { margin-left: 280px; }
.reportes_wrapper { max-width: 1600px; margin: 0 auto; }

/* ENCABEZADO MINIMALISTA */
.header_dashboard {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 20px;
}
.main_title { font-size: 1.8rem; font-weight: 800; margin: 0; }
.theme_dark .main_title { color: #FFFFFF; }
.theme_light .main_title { color: #333333; }
.sub_title { color: #99A2AD; font-size: 0.9rem; }

.header_selectors {
  display: flex;
  gap: 15px;
}
.input_compact {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 16px;
  gap: 10px;
  transition: all 0.2s;
}
.theme_light .input_compact { background: #FFFFFF; border: 1px solid #E0E0E0; box-shadow: 0 .125rem .25rem rgba(0,0,0,.075); }
.theme_dark .input_compact { background: #2B2B40; border: 1px solid #44475A; box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35); }
.input_compact:focus-within { border-color: #8A2BE2; box-shadow: 0 0 0 2px rgba(138, 43, 226, 0.3); }

.icon_purple { color: #8A2BE2; font-size: 1.1rem; }
.select_invisible { border: none; background: transparent; font-weight: 700; outline: none; font-size: 0.9rem; width: 160px; }
.theme_light .select_invisible { color: #333333; }
.theme_dark .select_invisible { color: #E4E6EB; }
.theme_dark .select_invisible option { background: #1E1E30; color: #E4E6EB; }

/* BARRA DE CONFIGURACIÓN */
.config_toolbar {
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
}
.theme_light .config_toolbar { background: #FFFFFF; border: 1px solid #E0E0E0; }
.theme_dark .config_toolbar { background: #2B2B40; border: 1px solid #44475A; }

.toolbar_top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.date_group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.date_input {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 10px;
  gap: 8px;
}
.theme_light .date_input { background: #F7F9FC; border: 1px solid #E0E0E0; }
.theme_dark .date_input { background: #3C3C55; border: 1px solid rgba(255, 255, 255, 0.05); }
.date_input input { border: none; background: transparent; outline: none; color: inherit; font-weight: 600; font-size: 0.9rem; }
.theme_dark .date_input input { color: #FFFFFF; color-scheme: dark; }

.view_toggles {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px;
  border-radius: 12px;
}
.theme_light .view_toggles { background: #F7F9FC; border: 1px solid #E0E0E0; }
.theme_dark .view_toggles { background: rgba(0,0,0,0.2); border: 1px solid rgba(255, 255, 255, 0.05); }

.divider { width: 1px; height: 20px; background: #99A2AD; opacity: 0.3; margin: 0 4px; }

.pill_btn {
  border: none;
  background: transparent;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  color: #99A2AD;
}
.theme_dark .pill_btn { color: #E0E0E0; }
.pill_btn.activo { background: #8A2BE2; color: #FFFFFF; box-shadow: 0 4px 12px rgba(125, 89, 255, 0.35); }
.pill_btn.optimizado.activo { background: #1ABC9C; box-shadow: 0 4px 12px rgba(26, 188, 156, 0.3); }
.pill_btn.puro.activo { background: #c69a13; color: #333333; box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3); }

.action_group {
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn_extract {
  background: linear-gradient(to right, #6F00FF, #A300FF);
  color: #FFFFFF;
  border: none;
  padding: 10px 24px;
  border-radius: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
}
.btn_extract:disabled { background: #7F8C8D; cursor: not-allowed; opacity: 0.5; }
.btn_extract:not(:disabled):hover { transform: translateY(-2px); filter: brightness(1.1); box-shadow: 0 4px 12px rgba(125, 89, 255, 0.35); }

/* PANEL DE LÍMITES */
.limits_panel {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed rgba(153, 162, 173, 0.3);
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.limits_title { font-size: 0.85rem; font-weight: 800; color: #8A2BE2; text-transform: uppercase; }
.limit_box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.limit_box label { font-size: 0.75rem; font-weight: 700; color: #99A2AD; }
.limit_input {
  width: 90px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid;
  font-weight: 700;
  font-size: 0.9rem;
  text-align: center;
}
.theme_light .limit_input { background: #F7F9FC; border-color: #E0E0E0; color: #333333; }
.theme_dark .limit_input { background: #3C3C55; border-color: rgba(255, 255, 255, 0.1); color: #FFFFFF; }

/* ETIQUETAS MÉTRICAS */
.metrics_bar {
  display: flex;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid rgba(153, 162, 173, 0.1);
}
.metrics_scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}
.metrics_scroll::-webkit-scrollbar { height: 4px; }
.metrics_scroll::-webkit-scrollbar-thumb { background: #99A2AD; border-radius: 4px; }

.metric_chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.theme_light .metric_chip { background: rgba(0,0,0,0.03); color: #333333; }
.theme_dark .metric_chip { background: rgba(255,255,255,0.05); color: #E4E6EB; }
.metric_chip:hover { background: rgba(138, 43, 226, 0.1); color: #8A2BE2; }
.metric_chip.activo { background: rgba(138, 43, 226, 0.15); border-color: #8A2BE2; color: #8A2BE2; }
.m_name { font-weight: 700; font-size: 0.85rem; }
.m_unit { font-size: 0.7rem; opacity: 0.7; }

/* SWITCH */
.switch_wrapper { display: flex; align-items: center; cursor: pointer; }
.switch { position: relative; display: inline-block; width: 40px; height: 22px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #7F8C8D; transition: .3s; border-radius: 34px; }
.slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: #FFFFFF; transition: .3s; border-radius: 50%; }
input:checked + .slider { background: linear-gradient(to right, #6F00FF, #A300FF); }
input:disabled + .slider { opacity: 0.5; cursor: not-allowed; }
input:checked + .slider:before { transform: translateX(18px); }

/* GRID GRAFICAS */
.dashboard_grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}
.grid_item { width: 100%; }
.span_2 { grid-column: span 2; }
.span_1 { grid-column: span 1; }

.empty_state { border-radius: 16px; }
.theme_light .empty_state { background: #FFFFFF; }
.theme_dark .empty_state { background: #2B2B40; }
.empty_icon { width: 80px; height: 80px; border-radius: 20px; background: rgba(138, 43, 226, 0.1); color: #8A2BE2; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; margin: 0 auto; }
.text_light { color: #333333; }
.theme_dark .text_light { color: #FFFFFF; }
.text_muted { color: #99A2AD; }

.shadow_soft { box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12); }
.alert_box { padding: 16px 20px; border-radius: 12px; font-weight: 700; margin-top: 10px; }
.alert_box.error { background: rgba(231, 76, 60, 0.1); color: #E74C3C; border: 1px solid rgba(231, 76, 60, 0.3); }

@media (max-width: 1200px) {
  .dashboard_grid { grid-template-columns: 1fr; }
  .span_1 { grid-column: span 1; }
  .span_2 { grid-column: span 1; }
  .toolbar_top { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 768px) {
  .plataforma_contenido { margin-left: 0; padding: 15px; }
  .header_dashboard { flex-direction: column; align-items: flex-start; }
  .date_group { flex-direction: column; align-items: stretch; width: 100%; }
  .action_group { width: 100%; justify-content: space-between; }
}
</style>