import { createApp } from 'vue'
import App from './App.vue'
import router from '@/router'
import '@/assets/scss/base-styles.scss'
import "@/assets/main.css";
// 🗺️ Estilos de Leaflet y controles
import 'leaflet/dist/leaflet.css'
import 'leaflet-control-geocoder/dist/Control.Geocoder.css'
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css'

// 🎨 Bootstrap y sus iconos
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap-icons/font/bootstrap-icons.css'

// window.API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import { API_BASE_URL } from '@/config';
window.API_BASE_URL = API_BASE_URL;


// 🧩 Font Awesome
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { 
  faBars, 
  faArrowCircleLeft, 
  faThLarge, 
  faFolder, 
  faTabletAlt, 
  faHeadphonesAlt, 
  faFileAlt, 
  faRuler, 
  faCog, 
  faSignOutAlt,
  faUserCircle,
  faMicrochip,
  faSignal 
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faBars, 
  faArrowCircleLeft, 
  faThLarge, 
  faFolder, 
  faTabletAlt, 
  faHeadphonesAlt, 
  faFileAlt, 
  faRuler, 
  faCog, 
  faSignOutAlt,
  faUserCircle,
  faMicrochip,
  faSignal
)

// 🚀 Crear la app Vue
const app = createApp(App)

// Registrar el componente global de FontAwesome
app.component('font-awesome-icon', FontAwesomeIcon)

// Activar router y montar app
app.use(router)
app.mount('#app')
