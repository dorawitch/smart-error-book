<template>
  <section class="panel rec-layout">
    <div class="left panel-inner">
      <h2>选择错题</h2>
      <div class="hint">选择一条错题后，系统会给出相似推荐</div>
      <div class="question-list">
        <button
          v-for="item in list"
          :key="item.id"
          class="question-btn"
          :class="{ active: selected && selected.id === item.id }"
          @click="pick(item)"
        >
          <span>ID {{ item.id }}</span>
          <small>{{ item.knowledge_point || "未标注" }}</small>
        </button>
      </div>
    </div>

    <div class="right panel-inner">
      <h2>推荐结果</h2>
      <div v-if="!selected" class="hint">请先从左侧选择一个题目</div>
      <div v-else>
        <p class="focus-title">当前题目：{{ selected.question }}</p>
        <button @click="runRecommend(selected.id)">生成推荐</button>
      </div>

      <div v-if="queried && !recs.length" class="hint">未命中相似题，已尝试低阈值重试。</div>

      <div class="rec-list" v-if="recs.length">
        <article v-for="r in recs" :key="r.id" class="rec-card">
          <p>{{ r.question }}</p>
          <small>{{ r.knowledge_point || "未标注" }} / {{ r.error_type || "未标注" }}</small>
          <small>分数 {{ typeof r.score === 'number' ? r.score.toFixed(3) : '-' }} | {{ r.confidence_level || 'unknown' }}</small>
        </article>
      </div>
    </div>
  </section>
</template>

<script>
import { fetchList, fetchRecommend } from "../services/api";

export default {
  data() {
    return {
      list: [],
      selected: null,
      recs: [],
      queried: false
    };
  },
  methods: {
    async loadSeed() {
      try {
        const res = await fetchList({ page: 1, page_size: 20 });
        this.list = res.items || [];
      } catch (err) {
        alert("加载题目失败");
      }
    },
    pick(item) {
      this.selected = item;
      this.recs = [];
      this.queried = false;
    },
    async runRecommend(id) {
      this.queried = true;
      try {
        let res = await fetchRecommend(id, { limit: 6, min_score: 0.22 });
        let items = res.recommendations || [];
        if (!items.length) {
          res = await fetchRecommend(id, { limit: 6, min_score: 0.08 });
          items = res.recommendations || [];
        }
        this.recs = items;
      } catch (err) {
        alert("推荐失败");
      }
    }
  },
  mounted() {
    this.loadSeed();
  }
};
</script>

<style scoped>
.rec-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 12px;
}

.panel-inner {
  border: 1px solid #e1ebf7;
  border-radius: 14px;
  padding: 12px;
  background: #fff;
}

.hint {
  color: #607792;
  margin: 8px 0;
}

.question-list {
  display: grid;
  gap: 8px;
  max-height: 560px;
  overflow: auto;
}

.question-btn {
  text-align: left;
  border: 1px solid #d6e3f3;
  background: #f8fbff;
  border-radius: 10px;
  padding: 10px;
  color: #234a70;
  cursor: pointer;
}

.question-btn.active {
  border-color: #2c8df4;
  background: #ebf4ff;
}

.question-btn span,
.question-btn small {
  display: block;
}

button {
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #1f8fff, #3569ff);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  padding: 10px 12px;
}

.focus-title {
  margin-top: 8px;
  color: #243a53;
}

.rec-list {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.rec-card {
  border: 1px solid #e1ebf7;
  border-radius: 12px;
  padding: 10px;
}

.rec-card p {
  margin: 0;
}

.rec-card small {
  display: block;
  margin-top: 4px;
  color: #5b7390;
}

@media (max-width: 980px) {
  .rec-layout {
    grid-template-columns: 1fr;
  }

  .question-list {
    max-height: 280px;
  }
}
</style>
