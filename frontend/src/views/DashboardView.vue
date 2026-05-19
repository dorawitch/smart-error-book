<template>
  <div class="dashboard-grid">
    <section class="panel">
      <h2>系统总览</h2>
      <div class="stats-row">
        <article class="stat-card">
          <p>错题总量</p>
          <strong>{{ stats.total }}</strong>
        </article>
        <article class="stat-card">
          <p>知识点类别</p>
          <strong>{{ stats.knowledge_top.length }}</strong>
        </article>
        <article class="stat-card">
          <p>错误类型类别</p>
          <strong>{{ stats.error_type_top.length }}</strong>
        </article>
      </div>
      <div class="tag-wrap">
        <span v-for="item in stats.knowledge_top" :key="item.name" class="tag">{{ item.name }} {{ item.count }}</span>
      </div>
    </section>

    <section class="panel">
      <h2>上传错题</h2>
      <div class="upload-form">
        <label class="file-field" :class="{ active: fileName }">
          <input type="file" accept="image/*" @change="selectFile" />
          <span>{{ fileName || "点击选择错题图片" }}</span>
        </label>
        <input v-model.trim="knowledge" placeholder="知识点（例：函数）" />
        <input v-model.trim="errorType" placeholder="错误类型（例：计算错误）" />
        <button :disabled="isUploading || !file" @click="upload">{{ isUploading ? "上传中..." : "上传并入库" }}</button>
      </div>
    </section>

    <section class="panel latest-panel">
      <h2>最新错题</h2>
      <div v-if="loading" class="hint">加载中...</div>
      <ul v-else class="latest-list">
        <li v-for="item in latest" :key="item.id">
          <p>{{ item.question || "（暂无文本）" }}</p>
          <small>{{ item.knowledge_point || "未标注" }} / {{ item.error_type || "未标注" }}</small>
        </li>
      </ul>
    </section>
  </div>
</template>

<script>
import { fetchList, fetchStats, uploadQuestion } from "../services/api";

export default {
  data() {
    return {
      stats: { total: 0, knowledge_top: [], error_type_top: [] },
      latest: [],
      file: null,
      knowledge: "",
      errorType: "",
      loading: false,
      isUploading: false
    };
  },
  computed: {
    fileName() {
      return this.file ? this.file.name : "";
    }
  },
  methods: {
    async loadData() {
      this.loading = true;
      try {
        const [stats, listResp] = await Promise.all([
          fetchStats(),
          fetchList({ page: 1, page_size: 6 })
        ]);
        this.stats = {
          total: stats.total || 0,
          knowledge_top: stats.knowledge_top || [],
          error_type_top: stats.error_type_top || []
        };
        this.latest = listResp.items || [];
      } catch (err) {
        alert("加载概览失败，请检查后端服务。");
      } finally {
        this.loading = false;
      }
    },
    selectFile(e) {
      this.file = e.target.files[0] || null;
    },
    async upload() {
      if (!this.file) return;
      const form = new FormData();
      form.append("image", this.file);
      form.append("knowledge_point", this.knowledge);
      form.append("error_type", this.errorType);

      this.isUploading = true;
      try {
        const res = await uploadQuestion(form);
        alert(res.msg || "上传成功");
        this.file = null;
        this.knowledge = "";
        this.errorType = "";
        await this.loadData();
      } catch (err) {
        alert(err?.response?.data?.error || "上传失败，请重试。");
      } finally {
        this.isUploading = false;
      }
    }
  },
  mounted() {
    this.loadData();
  }
};
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  gap: 14px;
}

.stats-row {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  background: linear-gradient(145deg, #1f8fff, #3d64ff);
  border-radius: 12px;
  padding: 12px;
  color: #fff;
}

.stat-card p {
  margin: 0;
  opacity: 0.86;
  font-size: 0.84rem;
}

.stat-card strong {
  font-size: 1.5rem;
}

.tag-wrap {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: #eaf4ff;
  border: 1px solid #c7dcf4;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.84rem;
  color: #18558f;
}

.upload-form {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

input {
  width: 100%;
  border: 1px solid #d5e1ef;
  background: #f9fbff;
  border-radius: 10px;
  padding: 10px;
  font-family: inherit;
}

.file-field {
  border: 1.5px dashed #8db4da;
  background: #f4f9ff;
  border-radius: 10px;
  min-height: 42px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.file-field.active {
  border-style: solid;
  border-color: #2e8ff6;
}

.file-field input {
  display: none;
}

button {
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #1f8fff, #3569ff);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

button:disabled {
  opacity: 0.55;
}

.latest-list {
  list-style: none;
  padding: 0;
  margin: 12px 0 0;
  display: grid;
  gap: 10px;
}

.latest-list li {
  border: 1px solid #e1ebf7;
  border-radius: 10px;
  padding: 10px;
}

.latest-list p {
  margin: 0;
}

.latest-list small {
  color: #5f7592;
}

@media (max-width: 980px) {
  .stats-row,
  .upload-form {
    grid-template-columns: 1fr;
  }
}
</style>
