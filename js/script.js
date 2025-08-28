/**
 * SMT - Sistema Completo de Navegação
 * Versão 3.0 - Todas as Seções Integradas
 */

// ==============================================
// CONFIGURAÇÕES GLOBAIS
// ==============================================
const CONFIG = {
  sliderInterval: 5000,
  sections: [
    'home',
    'solucoes',
    'quemsomos',
    'valores',
    'contato'
  ],
  defaultSection: 'home',
  sectionContainers: {
    home: 'home-container',
    solucoes: 'solucoes-container',
    quemsomos: 'quemsomos-container',
    valores: 'valores-container',
    contato: 'contato-container'
  }
};

// ==============================================
// INICIALIZAÇÃO PRINCIPAL
// ==============================================
document.addEventListener('DOMContentLoaded', function() {
  try {
    initNavigation();
    initScrollListener();
    loadAllSections().then(() => {
      initSlider();
      initComponents();
    });
  } catch (error) {
    console.error('Erro na inicialização:', error);
    showError(`Erro durante a inicialização: ${error.message}`);
  }
});

// ==============================================
// CARREGAMENTO DE SEÇÕES
// ==============================================
async function loadAllSections() {
  showLoading();
  
  try {
    for (const [section, containerId] of Object.entries(CONFIG.sectionContainers)) {
      const html = await fetchSection(section);
      document.getElementById(containerId).innerHTML = html;
    }
  } catch (error) {
    console.error('Erro ao carregar seções:', error);
    showError('Falha ao carregar conteúdo. Recarregue a página.');
    return Promise.reject(error);
  } finally {
    hideLoading();
  }
}

async function fetchSection(section) {
  const response = await fetch(`sections/${section}.html`);
  if (!response.ok) throw new Error(`Seção ${section} não encontrada`);
  return await response.text();
}

// ==============================================
// SISTEMA DE NAVEGAÇÃO
// ==============================================
function initNavigation() {
  // Navegação por clique
  document.addEventListener('click', function(e) {
    const link = e.target.closest('a[href^="#"]');
    if (link) {
      e.preventDefault();
      const section = link.getAttribute('href').substring(1);
      scrollToSection(section);
      updateActiveLink(link);
    }
  });

  // Navegação por histórico
  window.addEventListener('popstate', function() {
    const section = getCurrentSection();
    scrollToSection(section);
  });
}

function scrollToSection(section) {
  const element = document.getElementById(section);
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
    history.pushState(null, null, `#${section}`);
    document.title = `SMT - ${capitalizeFirstLetter(section)}`;
  }
}

function updateActiveLink(activeLink) {
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.classList.toggle('active', link === activeLink);
  });
}

// ==============================================
// SLIDER AUTOMÁTICO
// ==============================================
function initSlider() {
  const sliders = document.querySelectorAll('.slider-container');
  
  sliders.forEach(slider => {
    const slides = slider.querySelectorAll('.slide');
    const dots = slider.querySelectorAll('.slider-dot');
    let currentIndex = 0;
    let interval;

    function showSlide(index) {
      slides.forEach((slide, i) => {
        slide.classList.toggle('active', i === index);
      });
      dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
      });
    }

    function startSlider() {
      clearInterval(interval);
      interval = setInterval(() => {
        currentIndex = (currentIndex + 1) % slides.length;
        showSlide(currentIndex);
      }, CONFIG.sliderInterval);
    }

    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => {
        currentIndex = index;
        showSlide(currentIndex);
        startSlider();
      });
    });

    slider.addEventListener('mouseenter', () => clearInterval(interval));
    slider.addEventListener('mouseleave', startSlider);

    showSlide(0);
    startSlider();
  });
}

// ==============================================
// SCROLL SUAVE E OBSERVER
// ==============================================
function initScrollListener() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, {
    threshold: 0.1
  });

  document.querySelectorAll('section').forEach(section => {
    observer.observe(section);
  });
}

// ==============================================
// UTILITÁRIOS
// ==============================================
function getCurrentSection() {
  const hash = window.location.hash.substring(1);
  return CONFIG.sections.includes(hash) ? hash : CONFIG.defaultSection;
}

function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function showLoading() {
  const app = document.getElementById('app');
  if (app) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-overlay';
    loadingDiv.innerHTML = `
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>Carregando...</p>
      </div>
    `;
    app.appendChild(loadingDiv);
  }
}

function hideLoading() {
  const loader = document.querySelector('.loading-overlay');
  if (loader) loader.remove();
}

function showError(message) {
  const app = document.getElementById('app');
  if (app) {
    app.innerHTML = `
      <div class="error-container">
        <h2>Ocorreu um erro</h2>
        <p>${message}</p>
        <a href="#home" class="error-button">Voltar para Home</a>
      </div>
    `;
  }
}

// ==============================================
// INICIALIZADOR DE COMPONENTES
// ==============================================
function initComponents() {
  // Inicializa componentes específicos aqui
  console.log('Componentes inicializados');
}

// Fallback para DOM já carregado
if (document.readyState !== 'loading') {
  setTimeout(() => {
    initNavigation();
    initScrollListener();
    loadAllSections();
  }, 100);
}
