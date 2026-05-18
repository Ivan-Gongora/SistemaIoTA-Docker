<template>
  <div class="sidebar-plataforma" 
       :class="{ 'theme-dark': isDark, 'closed': !isOpen }">

    <!-- LOGO -->
    <div class="logo-container" @click="redirigirAPlataforma">
      <div class="logo-icon">⚡</div>
      <div class="logo-text" v-if="isOpen">
        <h1 class="mb-0">IoT Central</h1>
        <p class="mb-0">Centro Tecnológico QROo</p>
      </div>
    </div>

    <!-- PERFIL -->
    <div v-if="isOpen" class="usuario-perfil">
      <div class="avatar"><i class="bi bi-person-circle"></i></div>

      <div class="info-texto">
        <p class="nombre">{{ nombre || 'Usuario' }}</p>
      </div>
    </div>

    <div v-else class="usuario-perfil-closed">
      <div class="avatar"><i class="bi bi-person-circle"></i></div>
    </div>

    <!-- NAVEGACIÓN -->
    <h6 v-if="isOpen" class="nav-heading">NAVEGACIÓN</h6>

    <ul class="nav-list">
      <li>
        <router-link to="/plataforma" class="nav-link gradient" exact-active-class="active">
          <i class="bi bi-grid-fill"></i>
          <span v-if="isOpen">Panel de Control</span>
        </router-link>
      </li>

      <li v-for="item in menuItems" :key="item.path">
        <router-link 
          :to="item.path" 
          class="nav-link" 
          :title="item.label"
          active-class="active">
          <i :class="item.icon"></i>
          <span v-if="isOpen">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>

    <!-- FOOTER -->
    <div class="sidebar-footer">
      <hr>

      <router-link to="/configuracion" class="nav-link footer-link">
        <i class="bi bi-gear-fill"></i>
        <span v-if="isOpen">Configuración</span>
      </router-link>

      <button class="nav-link footer-link" @click="cerrarSesion">
        <i class="bi bi-box-arrow-right"></i>
        <span v-if="isOpen">Cerrar Sesión</span>
      </button>
    </div>

  </div>
</template>


<script>
// Asegúrate de que Font Awesome (u otro ícono pack) esté incluido en tu proyecto
export default {
  name: 'BarraLateralPlataforma',
  props: {
    isOpen: { 
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      // Estado para la detección de modo oscuro
      isDark: false, 
      
      nombre: '',
      tipo_usuario: '', // Usaremos tipo_usuario directamente
      
      menuItems: [
                // Grupo 1: Administración y Gestión
                { path: '/mis-proyectos', label: 'Mis Proyectos', icon: 'bi bi-folder-fill' }, 
                { path: '/dispositivos', label: 'Dispositivos', icon: 'bi bi-tablet-fill' }, 
                { path: '/sensores', label: 'Sensores', icon: 'bi bi-graph-up' }, 
                { path: '/unidades', label: 'Unidades de Medida', icon: 'bi bi-rulers' }, 
                { path: '/vista-csv', label: 'Carga CSV', icon: 'bi bi-file-earmark-arrow-up' },
                { path: '/analisis-avanzado', label: 'Análisis Avanzado', icon: 'bi bi-funnel-fill' },
                
                // Se usa una ruta vacía o un elemento sin etiqueta para crear una separación visual
                { path: '', label: '', icon: 'divider-space' }, 

                // Grupo 2: Análisis y Reportes
                // Datos Históricos (Tu vista actual de reportes)
                {path: '/tiempo-real', label: 'Datos en Tiempo Real', icon: 'bi bi-clock-history' },

                { path: '/reportes', label: 'Datos Históricos', icon: 'bi bi-bar-chart-line-fill' }, 

                {path: '/menu-gestion-datos-energeticos', label: 'Gestión de Datos Energéticos', icon: 'bi bi-lightning-fill' },
                 
                // // Análisis Avanzado
                // { path: '/analisis', label: 'Análisis Avanzado', icon: 'bi bi-funnel-fill' }, 
                
                // // Predicción de Gastos (Función Gemini)
                // { path: '/prediccion-gastos', label: 'Predicción de Gastos', icon: 'bi bi-robot' }, 

                //  // Reportes Generados
                // { path: '/reportes-generados', label: 'Reportes Generados', icon: 'bi bi-file-earmark-bar-graph' }, 
            ]
    };
  },
  mounted() {
    // 1. Cargar datos del usuario
    const resultado = JSON.parse(localStorage.getItem('resultado'));
    if (resultado && resultado.usuario) {
      this.nombre = resultado.usuario.nombre + ' ' + resultado.usuario.apellido;
    }
    
    // 2. Inicializar la detección de tema
    this.detectarTemaSistema();
    
    // 3. Añadir listener para cambios de tema
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleThemeChange);
    }
  },
   beforeUnmount() { // 👈 CORRECCIÓN A beforeUnmount
    // Limpiar el listener al destruir el componente
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleThemeChange);
    }
  },
  methods: {
    redirigirAPlataforma() {
      this.$router.push('/plataforma');
    },
    cerrarSesion() {
      // Lógica de logout: Eliminar token/datos y redirigir
      localStorage.removeItem('accessToken'); // O 'currentUser', o 'resultado'
      this.$router.push('/');
    },
    handleThemeChange(event) {
      this.isDark = event.matches;
    },
    detectarTemaSistema() {
      // Detección inicial
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.isDark = true;
      } else {
        this.isDark = false;
      }
    }
  }
};
</script>

<style scoped lang="scss">

// -----------------------------
// SIDEBAR BASE
// -----------------------------
.sidebar-plataforma {
  width: $WIDTH-SIDEBAR;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  padding: 22px 18px;
  overflow-y: auto;
  background: $WHITE-SOFT;
  transition: width .25s ease, background .3s;
  box-sizing: border-box;
  z-index: 1000;

  &::-webkit-scrollbar { width: 0; }

  &.closed {
    width: $WIDTH-CLOSED;

    span { opacity: 0; pointer-events: none; }

    .nav-link { justify-content: center; }
    .footer-link { justify-content: center; }
  }
}

// -----------------------------
// LOGO
// -----------------------------
.logo-container {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  cursor: pointer;

  .logo-icon {
    font-size: 28px;
    padding: 8px;
    border-radius: 10px;
    background: $GRADIENT;
    color: white;
    box-shadow: $shadow-purple;
    margin-right: 12px;
  }

  .logo-text {
    h1 { font-size: 1.2rem; font-weight: 700; }
    p { font-size: .8rem; opacity: .85; }
  }
}

// -----------------------------
// PERFIL
// -----------------------------
.usuario-perfil,
.usuario-perfil-closed {
  display: flex;
  align-items: center;
  margin-bottom: 20px;  // antes 25px → más compacto

  .avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;

    i {
      font-size: 30px;
      color: $PRIMARY-PURPLE;
    }
  }
}

.usuario-perfil {
  padding: 14px;
  border-radius: 12px;
  background: $SUBTLE-BG-LIGHT;
  box-shadow: $shadow-soft;

  .info-texto {
    margin-left: 12px;

    .nombre { font-weight: 600; }
    .rol { opacity: .6; font-size: .82rem; }
  }
}

.usuario-perfil-closed { justify-content: center; }

// -----------------------------
// NAVEGACIÓN
// -----------------------------
.nav-heading {
  font-size: .75rem;
  margin: 0 0 10px 10px; // más compacto
  opacity: .7;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

// LINKS BASE
.nav-link {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 4px; // antes 6px → más compacto
  text-decoration: none;
  color: $DARK-TEXT;
  transition: background .2s, color .2s;
  

  i {
    width: 26px;
    text-align: center;
    margin-right: 10px;
    font-size: 1.1rem;
  }

  &:hover {
    background: $hover-light;
  }

  &.active {
    color: $ACCENT-COLOR;
    font-weight: 600;
  }

  &.gradient {
    background: $GRADIENT;
    color: white;
    box-shadow: $shadow-purple;
    font-weight: bold;

    &:hover { opacity: .9; }
  }

}

// -----------------------------
// FOOTER – AJUSTADO
// -----------------------------
.sidebar-footer {
  margin-top: 16px !important;   // ANTES auto → demasiado lejos
  padding-top: 8px;
  border-top: 1px solid rgba(0,0,0,0.08); // separación más suave

  hr { opacity: .4; margin: 12px 0; }

  .footer-link {
    margin-bottom: 6px;
    padding: 10px 12px;
    border-radius: 10px;

    &:hover { background: $hover-light; }
  }

  button.footer-link {
    background: transparent;
    border: none;
    width: 100%;
    text-align: left;
    cursor: pointer;
  }
}

// -----------------------------
// BOTÓN PARA CERRAR SIDEBAR EN MÓVIL
// -----------------------------
.sidebar-close-btn-expanded {
  display: none;
  padding: 10px;
  border-radius: 10px;
  margin-top: 14px;
  background: $hover-light;
  text-align: center;
  cursor: pointer;

  &:hover { background: $hover-light; }
}

// -----------------------------
// RESPONSIVE (MÓVIL / TABLET)
// -----------------------------
@media (max-width: 768px) {

  .sidebar-plataforma {
    padding: 18px 16px;
  }

  .sidebar-footer {
    margin-top: 20px !important;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.1);
  }

  // Botón para cerrar cuando está expandido
  .sidebar-close-btn-expanded {
    display: block !important;
  }
}

// -----------------------------
// MODO OSCURO / CLARO
// -----------------------------
.theme-dark {
  background: $BLUE-MIDNIGHT;
  color: $LIGHT-TEXT;

  .nav-link { color: $LIGHT-TEXT; &:hover { background: $dark-hover; } }
  .nav-heading { color: $GRAY-COLD; }
  .usuario-perfil { background: $SUBTLE-BG-DARK; }
}

</style>
