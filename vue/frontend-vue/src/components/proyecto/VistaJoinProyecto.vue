<template>
  <div class="join-project-view">
    <div class="join-box" :class="{ 'theme-dark': isDark }">
      <h2>Uniéndote al Proyecto...</h2>
      
      <div v-if="loading" class="estado-mensaje loading">
        <i class="fas fa-spinner fa-spin"></i> Validando invitación y uniéndote...
      </div>
      
      <div v-if="success" class="estado-mensaje success">
        <i class="bi bi-check-circle-fill"></i> {{ success }}
        <p>Serás redirigido al proyecto en 3 segundos.</p>
      </div>
      
      <div v-if="error" class="estado-mensaje error">
        <i class="bi bi-x-octagon-fill"></i> {{ error }}
        <p v-if="error.includes('expirada')">Por favor, pida a su administrador un nuevo link.</p>
      </div>
      
    </div>
  </div>
</template>

<script>
// const API_BASE_URL = 'http://127.0.0.1:8001';

export default {
    name: 'VistaJoinProyecto',
    data() {
        return {
            isDark: false,
            loading: true,
            error: null,
            success: null,
        };
    },
    mounted() {
        this.detectarTemaSistema();
        this.processJoin();
    },
    methods: {
        async processJoin() {
            // 1. Obtener el token de invitación de la URL
            const inviteToken = this.$route.query.token;
            const accessToken = localStorage.getItem('accessToken');

            if (!inviteToken) {
                this.error = 'Token de invitación no encontrado en la URL.';
                this.loading = false;
                return;
            }

            if (!accessToken) {
                // Esto no debería suceder gracias al Navigation Guard, pero es seguro.
                this.error = 'Debes iniciar sesión antes de aceptar una invitación.';
                this.loading = false;
                this.$router.push('/');
                return;
            }

            // 2. Llamar al endpoint de FastAPI para procesar el token
            try {
                const response = await fetch(`${API_BASE_URL}/api/join-project/${inviteToken}`, {
                    method: 'POST',
                    headers: {
                        // 🚨 CRÍTICO: Enviamos el token de SESIÓN para que FastAPI identifique al usuario
                        'Authorization': `Bearer ${accessToken}`, 
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || data.message || 'Fallo al procesar la invitación.');
                }

                // Éxito
                this.success = data.message || 'Unión al proyecto completada.';
                
                // Redirigir al proyecto o a la lista de proyectos después de 3 segundos
                setTimeout(() => {
                    this.$router.push('/mis-proyectos');
                }, 3000);

            } catch (err) {
                this.error = err.message.includes('Credenciales inválidas o token expirado') 
                             ? 'Invitación expirada o inválida.' 
                             : err.message;
            } finally {
                this.loading = false;
            }
        },
        detectarTemaSistema() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.isDark = true;
            }
        },
    }
};
</script>

<style scoped lang="scss">
// ----------------------------------------
// VARIABLES DE LA PALETA
// ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2; 
// $SUCCESS-COLOR: #1ABC9C;  
// $ERROR-COLOR: #FF5733;    
// $WHITE-SOFT: #F7F9FC;     
// $BLUE-MIDNIGHT: #1A1A2E;  
// $SUBTLE-BG-DARK: #2B2B40; 
// $DARK-TEXT: #333333;
//  CRÍTICO: Esta variable faltaba en el ámbito del componente
// $LIGHT-TEXT: #E4E6EB;  
.join-project-view {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    width: 100%;
}

.join-box {
    width: 100%; max-width: 450px;
    padding: 30px; border-radius: 15px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    
    h2 { margin-bottom: 25px; font-weight: 600; }
}

.estado-mensaje {
    padding: 20px; border-radius: 8px; font-size: 1.1rem;
    i { margin-right: 10px; }
    p { margin-top: 10px; font-size: 0.9rem; opacity: 0.8; }
}

.loading { background-color: rgba($PRIMARY-PURPLE, 0.1); color: $PRIMARY-PURPLE; }
.success { background-color: rgba($SUCCESS-COLOR, 0.1); color: $SUCCESS-COLOR; }
.error { background-color: rgba($ERROR-COLOR, 0.1); color: $ERROR-COLOR; }


// TEMAS
.theme-light .join-box { background-color: $WHITE-SOFT; }
.theme-dark .join-box { 
    background-color: $SUBTLE-BG-DARK; 
    color: $LIGHT-TEXT;
}
.theme-dark .loading { background-color: rgba($PRIMARY-PURPLE, 0.3); color: $LIGHT-TEXT; }
.theme-dark .error { background-color: rgba($ERROR-COLOR, 0.3); }
</style>