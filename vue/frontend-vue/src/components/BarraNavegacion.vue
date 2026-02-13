<template>
  <nav class="navbar navbar-expand-lg fixed-top custom-nav" :class="{ 'scrolled': isScrolled }">
    <div class="container">
      
      <a class="navbar-brand d-flex align-items-center gap-2" href="#">
        <div class="logo-icon">
          <i class="bi bi-cpu-fill"></i>
        </div>
        <span class="brand-text">Plataforma IoT</span>
      </a>

      <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navegacionPrincipal">
        <i class="bi bi-list fs-2 toggle-icon"></i>
      </button>

      <div class="collapse navbar-collapse" id="navegacionPrincipal">
        <ul class="navbar-nav ms-auto align-items-center">
          <li class="nav-item">
            <a class="nav-link custom-link" href="#">Acerca de</a>
          </li>
          <li class="nav-item ms-lg-3">
            <router-link to="/registros" class="btn-nav-outline">
              Registrarse
            </router-link>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'BarraNavegacion',
  data() { return { isScrolled: false } },
  mounted() { window.addEventListener('scroll', this.handleScroll); },
  unmounted() { window.removeEventListener('scroll', this.handleScroll); },
  methods: {
    handleScroll() { this.isScrolled = window.scrollY > 20; }
  }
}
</script>
  
<style scoped>
/* NAV BASE */
.custom-nav {
  padding: 1.5rem 0;
  transition: all 0.3s ease;
  background: transparent;
}

.custom-nav.scrolled {
  background: var(--nav-bg-scrolled); /* Variable Adaptable */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--card-shadow);
}

/* LOGO */
.logo-icon {
  width: 35px; height: 35px;
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: #fff;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem;
}

.brand-text {
  color: var(--text-main);
  font-weight: 700;
  font-size: 1.2rem;
}

/* LINKS */
.custom-link {
  color: var(--text-muted) !important;
  font-weight: 500;
  transition: color 0.3s;
}

.custom-link:hover {
  color: var(--primary) !important;
}

/* Icono Toggler (Móvil) */
.toggle-icon { color: var(--text-main); }

/* BOTÓN REGISTRO */
.btn-nav-outline {
  color: var(--text-main);
  background: transparent;
  border: 1px solid var(--border-color);
  padding: 8px 20px;
  border-radius: 50px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-nav-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: rgba(124, 58, 237, 0.05);
}
</style>