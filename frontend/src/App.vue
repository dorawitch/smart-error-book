<template>
  <div class="layout-shell">
    <aside class="sidebar">
      <div class="brand">
        <p class="brand-eyebrow">Smart Error Book</p>
        <h1>智能错题本</h1>
      </div>

      <nav class="nav-list">
        <RouterLink to="/dashboard" class="nav-item">概览</RouterLink>
        <RouterLink to="/questions" class="nav-item">题库管理</RouterLink>
        <RouterLink to="/recommend" class="nav-item">智能推荐</RouterLink>
      </nav>
    </aside>

    <section class="main-pane">
      <header class="topbar">
        <div>
          <p class="topbar-title">{{ currentTitle }}</p>
          <p class="topbar-sub">把功能分层，操作更聚焦</p>
        </div>
      </header>

      <main class="content-wrap">
        <RouterView />
      </main>
    </section>
  </div>
</template>

<script>
export default {
  computed: {
    currentTitle() {
      return this.$route?.meta?.title || "智能错题本";
    }
  }
};
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap");

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: "Outfit", "Noto Sans SC", sans-serif;
  background: linear-gradient(140deg, #f4f8ff 0%, #f7fbf9 50%, #fff7ef 100%);
  color: #1f2d3d;
}

#app {
  min-height: 100vh;
}

.layout-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px 1fr;
}

.sidebar {
  padding: 24px 16px;
  border-right: 1px solid #e5edf7;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
}

.brand-eyebrow {
  margin: 0;
  font-size: 0.78rem;
  color: #6c7d93;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.brand h1 {
  margin: 6px 0 0;
  font-size: 1.35rem;
}

.nav-list {
  margin-top: 24px;
  display: grid;
  gap: 8px;
}

.nav-item {
  text-decoration: none;
  color: #285074;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  font-weight: 600;
}

.nav-item.router-link-active {
  background: #eaf4ff;
  border-color: #c9ddf5;
  color: #195a99;
}

.main-pane {
  display: grid;
  grid-template-rows: auto 1fr;
}

.topbar {
  padding: 18px 24px;
}

.topbar-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
}

.topbar-sub {
  margin: 4px 0 0;
  font-size: 0.9rem;
  color: #637a94;
}

.content-wrap {
  padding: 0 24px 24px;
}

.panel {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e6eef8;
  border-radius: 18px;
  box-shadow: 0 16px 34px rgba(27, 58, 88, 0.08);
  padding: 18px;
}

.panel h2 {
  margin: 0;
  font-size: 1.15rem;
}

@media (max-width: 980px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid #e5edf7;
  }

  .nav-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
