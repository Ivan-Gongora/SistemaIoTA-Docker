<template>
  <div class="hero-container">
    <div class="container position-relative z-1">
      <div class="row align-items-center justify-content-center min-vh-80">
        
        <div class="col-lg-6 mb-5 mb-lg-0 pe-lg-5 text-center text-lg-start">
          
          <div class="d-flex gap-2 mb-4 justify-content-center justify-content-lg-start flex-wrap">
            <span class="tech-pill"><span class="dot"></span> IoT</span>
            <span class="tech-pill"><i class="bi bi-lightning-charge-fill"></i> Eficiencia</span>
            <span class="tech-pill"><i class="bi bi-graph-up"></i> Análisis</span>
          </div>

          <h1 class="display-4 fw-bold mb-3 text-main-gradient">
            Gestión Energética <br> Inteligente
          </h1>
          
          <p class="lead text-description mb-4">
            Plataforma de monitoreo para la optimización del consumo eléctrico en el 
            <strong>TecNM Campus Chetumal</strong>. Detecta patrones y reduce costos operativos.
          </p>

          <ul class="feature-list d-inline-block text-start">
            <li><i class="bi bi-check-circle-fill text-accent"></i> Detección de fugas energéticas</li>
            <li><i class="bi bi-check-circle-fill text-accent"></i> Monitoreo de sensores en vivo</li>
            <li><i class="bi bi-check-circle-fill text-accent"></i> Reportes automatizados</li>
          </ul>
        </div>

        <div class="col-lg-5 col-xl-4">
          <div class="login-card">
            
            <div class="text-center mb-4">
              <div class="avatar-glow mb-3">
                <i class="bi bi-person-fill"></i>
              </div>
              <h3 class="fw-bold card-heading">Acceso Administrativo</h3>
              <p class="text-muted small">Ingresa tus credenciales institucionales</p>
            </div>

            <form @submit.prevent="iniciarSesion">
              <div class="mb-3">
                <label class="input-label">USUARIO</label>
                <div class="custom-input-group">
                  <span class="input-icon"><i class="bi bi-person"></i></span>
                  <input type="text" class="clean-input" v-model="usuario" placeholder="Ej. admin_tecnm" required>
                </div>
              </div>

<div class="mb-4">
  <label class="input-label">CONTRASEÑA</label>
  <div class="custom-input-group d-flex align-items-center"> <span class="input-icon"><i class="bi bi-lock"></i></span>
    
    <input 
      :type="mostrarContrasena ? 'text' : 'password'" 
      class="clean-input" 
      v-model="contrasena" 
      placeholder="••••••••" 
      required
    >
    
    <span 
      class="input-icon toggle-password" 
      @click="mostrarContrasena = !mostrarContrasena"
      style="cursor: pointer; margin-left: 10px;"
      title="Mostrar/Ocultar contraseña"
    >
      <i class="bi" :class="mostrarContrasena ? 'bi-eye-fill' : 'bi-eye-slash-fill'"></i>
    </span>

  </div>
</div>


              <div v-if="error" class="alert alert-danger py-2 small mb-3">
                {{ error }}
              </div>

              <button type="submit" class="btn-primary-custom w-100" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loading ? 'Conectando...' : 'Entrar' }}
              </button>
            </form>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
// Ajusta tu lógica de script original aquí...
export default {
  name: 'SeccionPrincipal',
  data() { return { usuario: '', contrasena: '',mostrarContrasena: false, error: '', loading: false }; },
 methods: {
    async iniciarSesion() {
      this.error = '';
      if (!this.usuario || !this.contrasena) {
        this.error = 'Campos incompletos.';
        return;
      }

      this.loading = true;
      try {
        const response = await fetch(`${API_BASE_URL}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            nombre_usuario: this.usuario, 
            contrasena: this.contrasena 
          })
        });

        const resultado = await response.json();
        
        if (!response.ok) {
          throw new Error(resultado.detail || 'Credenciales incorrectas');
        }

        if (resultado.access_token) {
          localStorage.setItem('accessToken', resultado.access_token);
          localStorage.setItem('resultado', JSON.stringify(resultado));
          this.$router.push('/plataforma');
        } else {
          throw new Error('Error de servidor: Token no recibido.');
        }
        
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<!-- <script>
// Ajusta la URL según tu entorno
// const API_BASE_URL = 'http://127.0.0.1:8001'; 

export default {
  name: 'SeccionPrincipal',
  data() {
    return {
      usuario: '',
      contrasena: '',
      error: '',
      loading: false
    };
  },
  methods: {
    async iniciarSesion() {
      this.error = '';
      if (!this.usuario || !this.contrasena) {
        this.error = 'Campos incompletos.';
        return;
      }

      this.loading = true;
      try {
        const response = await fetch(`${API_BASE_URL}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            nombre_usuario: this.usuario, 
            contrasena: this.contrasena 
          })
        });

        const resultado = await response.json();
        
        if (!response.ok) {
          throw new Error(resultado.detail || 'Credenciales incorrectas');
        }

        if (resultado.access_token) {
          localStorage.setItem('accessToken', resultado.access_token);
          localStorage.setItem('resultado', JSON.stringify(resultado));
          this.$router.push('/plataforma');
        } else {
          throw new Error('Error de servidor: Token no recibido.');
        }
        
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script> -->

<style scoped>
.hero-container {
  min-height: 85vh;
  display: flex;
  align-items: center;
  position: relative;
}

/* TEXTOS */
.text-main-gradient {
  color: var(--text-main);
  /* Opcional: Gradiente sutil solo en dark mode si quieres */
}

.text-description { color: var(--text-muted); }
.text-accent { color: var(--accent); }
.card-heading { color: var(--text-main); }

/* BADGES */
.tech-pill {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 5px 15px;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 600;
  display: flex; align-items: center; gap: 8px;
}
.dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; }

/* LISTA */
.feature-list { list-style: none; padding: 0; }
.feature-list li {
  margin-bottom: 10px;
  color: var(--text-muted);
  display: flex; align-items: center; gap: 10px;
}

/* LOGIN CARD ADAPTABLE */
.login-card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: var(--glass-border);
  border-radius: 24px;
  padding: 2.5rem;
  box-shadow: var(--card-shadow);
  .toggle-password:hover {
  color: #000;
}
}


.avatar-glow {
  width: 60px; height: 60px;
  background: rgba(124, 58, 237, 0.1);
  color: var(--primary);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem;
  margin: 0 auto;
}

/* INPUTS */
.input-label {
  font-size: 0.7rem; font-weight: 700; color: var(--text-muted); margin-bottom: 5px;
}

.custom-input-group {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  display: flex; align-items: center;
  transition: all 0.3s;
}

.custom-input-group:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

.input-icon { padding: 0 15px; color: var(--text-muted); }

.clean-input {
  width: 100%; background: transparent; border: none;
  color: var(--text-main);
  padding: 12px 10px 12px 0;
  outline: none;
}
.clean-input::placeholder { color: var(--text-muted); opacity: 0.5; }

/* BOTÓN */
.btn-primary-custom {
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: #fff;
  border: none; padding: 12px; border-radius: 12px;
  font-weight: 600; transition: transform 0.2s;
}
.btn-primary-custom:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(124, 58, 237, 0.3);
}
</style>