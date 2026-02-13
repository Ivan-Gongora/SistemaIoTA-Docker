import { createRouter, createWebHistory } from 'vue-router';
// ----------------------------------------------------------------
//  ❌ CAMBIA ESTAS IMPORTACIONES:
// ----------------------------------------------------------------
import VistaPrincipal from '@/components/VistaPrincipal.vue'; // Antes: ../components/VistaPrincipal.vue
import VistaRegistro from '@/components/login/VistaRegistro.vue'; // Antes: ../components/login/VistaRegistro.vue
import VistaPlataformaPrincipal from '@/components/plataforma/VistaPlataformaPrincipal.vue';
import VistaDispositivos from '@/components/dispositivos/VistaDispositivosGeneral.vue';
import DetalleDispositivo from '@/components/dispositivos/DetalleDispositivo.vue';
import VistaMisProyectos from '@/components/proyecto/VistaMisProyectos.vue';
import DetalleProyecto from '@/components/proyecto/DetalleProyecto.vue'
import MenuSimulacion from '@/components/simulador/VistaSimulacionMenu.vue';
import VistaC from '@/components/simulador/csvEnviar.vue';
import MenuGestion from '@/components/GestionDB/VistaGestionMenu.vue'
import VerValores from '@/components/valores/VerValores.vue';
import updateValores from '@/components/valores/updateValores.vue';
import VistaJoinProyecto from '@/components/proyecto/VistaJoinProyecto.vue';
import VistaGeneralUnidades from '@/components/unidades/VistaUnidadesMedida.vue';
import DetalleSensor from '@/components/sensores/DetalleSensor.vue';
import GeneralSensores from '@/components/sensores/VistaSensoresGeneral.vue';
import VistaReportes from '@/components/reportes/VistaReportes.vue';
import MenuGestionDatosEnergeticos from '@/components/reportes/VistaGestionDatosEnergeticos.vue';
import VistaSimuladorEnergetico from '@/components/reportes/VistaSimuladorEnergetico.vue';
import VistaResumenEstadistico from '@/components/reportes/VistaResumenEstadistico.vue';
import VistaTiempoReal from '@/components/reportes/VistaTiempoReal.vue';
// ----------------------------------------------------------------
// ... el resto de tu código de rutas y router

const routes = [
  {
    path: '/',
    name: 'Inicio',
    component: VistaPrincipal
  },
  {
    path: '/registros',
    name: 'Registros',
    component: VistaRegistro
  },
  {
    path: '/plataforma',
    name: 'Plataforma',
    component: VistaPlataformaPrincipal
  },
  {
    path: '/mis-proyectos',
    name: 'VistaMisProyectos',
    component: VistaMisProyectos
  },
  {
    path: '/detalle-proyecto/:id',
    name: 'DetalleProyecto',
    component: DetalleProyecto
  },
  {
    path: '/dispositivos',
    name: 'VistaDispositivos',
    component: VistaDispositivos
  },
  {
    path: '/detalle-dispositivo/:id',
    name: 'DetalleDispositivo',
    component: DetalleDispositivo
  },
  {
    path: '/menu-simulacion',
    name: 'MenuSimulacion',
    component: MenuSimulacion
  },
  {
    path: '/vista-csv',
    name: 'VistaCsv',
    component: VistaC
  },
  {
    path: '/menu-gestion',
    name: 'MenuGestion',
    component: MenuGestion
  },
  {
    path: '/vista_valores',
    name: 'VerValores',
    component: VerValores
  },
  {
    path: '/actualizar_valores',
    name: 'updateValores',
    component: updateValores
  },
  {
    path: '/join', 
    name: 'JoinProject', // Nombre clave para el guardia
    component: VistaJoinProyecto,
    
  },
  {
    path: '/unidades',
    name: 'VistaGeneralUnidades',
    component: VistaGeneralUnidades
  },
  {
        path: '/detalle-sensor/:id',
        name: 'DetalleSensor', // Nombre que usarás para navegar si usas { name: 'DetalleSensor', params: { id: ... } }
        component: DetalleSensor
    },
    {
        path: '/sensores',
        name: 'GeneralSensores',
        component: GeneralSensores
    },
    {
        path: '/reportes', // Ruta principal de reportes
        name: 'VistaReportes',
        component: VistaReportes
    },
    {
      path: '/menu-gestion-datos-energeticos',
      name: 'MenuGestionDatosEnergeticos',
      component: MenuGestionDatosEnergeticos
    },
    {
      path: '/simulador-energetico',
      name: 'VistaSimuladorEnergetico',
      component: VistaSimuladorEnergetico
    },
    {
      path: '/resumen-estadistico',
      name: 'VistaResumenEstadistico',
      component: VistaResumenEstadistico
    },
    {
      path: '/tiempo-real',
      name: 'VistaTiempoReal',
      component: VistaTiempoReal
    }
    
    
    
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// -----------------------------------------------------
// IMPLEMENTACIÓN DEL GUARDIA DE NAVEGACIÓN (JWT)
// -----------------------------------------------------

// 🚨 1. Lista de rutas protegidas (usando los 'name' definidos en el array 'routes')
const protectedRoutes = [
    'Plataforma', 
    'VistaMisProyectos', 
    'DetalleProyecto', 
    'VistaDispositivos', 
    'DetalleDispositivo',
    'MenuSimulacion', 
    'VistaCsv', 
    'MenuGestion', 
    'VerValores', 
    'updateValores',
    'JoinProject',
    'unidades',
    'VistaJoinProyecto',
    'VistaGeneralUnidades', 
    'MenuGestion',
    'DetalleSensor',
    'GeneralSensores',
    'VistaReportes',
    'MenuGestionDatosEnergeticos',
    'VistaSimuladorEnergetico',
    'VistaResumenEstadistico',
    'VistaTiempoReal'

];

// 🚨 2. Implementación del Navigation Guard
router.beforeEach((to, from, next) => {
    // Verifica si la ruta destino está en la lista de rutas protegidas
    if (protectedRoutes.includes(to.name)) {
        // Intenta obtener el token que se guardó en el login
        const token = localStorage.getItem('accessToken');

        if (token) {
            // El token existe: permite la navegación a la ruta solicitada
            next();
        } else {
            // El token NO existe: redirige a la ruta de inicio ('/')
            console.warn('Acceso denegado. Se requiere iniciar sesión.');
            next('/'); 
        }
    } else {
        // La ruta no está protegida (ej: Inicio o Registros): permite el acceso
        next();
    }
});

export default router;