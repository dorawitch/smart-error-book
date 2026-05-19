<template>
  <section class="panel">
    <div class="head-row">
      <h2>题库管理</h2>
      <span>共 {{ total }} 条</span>
    </div>

    <div class="filter-row">
      <input v-model.trim="filters.keyword" placeholder="关键字" @keyup.enter="search" />
      <input v-model.trim="filters.knowledge_point" placeholder="知识点" @keyup.enter="search" />
      <input v-model.trim="filters.error_type" placeholder="错误类型" @keyup.enter="search" />
      <button @click="search">查询</button>
    </div>

    <div v-if="loading" class="hint">加载中...</div>
    <div v-else-if="!list.length" class="hint">暂无数据</div>

    <div v-else class="list-wrap">
      <article v-for="item in list" :key="item.id" class="item-card">
        <div class="item-head">
          <span class="badge">ID {{ item.id }}</span>
          <div class="actions">
            <button class="light" @click="openEdit(item)">编辑</button>
            <button class="danger" @click="remove(item.id)">删除</button>
          </div>
        </div>
        <p>{{ item.question }}</p>
        <small>{{ item.knowledge_point || "未标注" }} / {{ item.error_type || "未标注" }}</small>
      </article>

      <div class="pager">
        <button class="light" :disabled="page <= 1" @click="load(page - 1)">上一页</button>
        <span>第 {{ page }} 页</span>
        <button class="light" :disabled="!hasNext" @click="load(page + 1)">下一页</button>
      </div>
    </div>

    <div v-if="showEdit" class="modal" @click.self="showEdit = false">
      <div class="modal-body panel">
        <h2>编辑错题</h2>
        <textarea v-model.trim="editing.question" rows="4"></textarea>
        <input v-model.trim="editing.knowledge_point" placeholder="知识点" />
        <input v-model.trim="editing.error_type" placeholder="错误类型" />
        <div class="actions right">
          <button class="light" @click="showEdit = false">取消</button>
          <button @click="save">保存</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { deleteQuestion, fetchList, updateQuestion } from "../services/api";

export default {
  data() {
    return {
      list: [],
      total: 0,
      page: 1,
      hasNext: false,
      loading: false,
      filters: { keyword: "", knowledge_point: "", error_type: "" },
      showEdit: false,
      editing: {}
    };
  },
  methods: {
    async load(targetPage = 1) {
      this.loading = true;
      try {
        const res = await fetchList({
          page: targetPage,
          page_size: 10,
          keyword: this.filters.keyword || undefined,
          knowledge_point: this.filters.knowledge_point || undefined,
          error_type: this.filters.error_type || undefined
        });
        this.list = res.items || [];
        this.total = res.total || 0;
        this.page = res.page || targetPage;
        this.hasNext = !!res.has_next;
      } catch (err) {
        alert("加载失败");
      } finally {
        this.loading = false;
      }
    },
    search() {
      this.load(1);
    },
    openEdit(item) {
      this.editing = { ...item };
      this.showEdit = true;
    },
    async save() {
      try {
        await updateQuestion(this.editing.id, {
          question: this.editing.question,
          knowledge_point: this.editing.knowledge_point,
          error_type: this.editing.error_type,
          answer: this.editing.answer
        });
        this.showEdit = false;
        await this.load(this.page);
      } catch (err) {
        alert("保存失败");
      }
    },
    async remove(id) {
      if (!window.confirm("确定删除该错题吗？")) return;
      try {
        await deleteQuestion(id);
        await this.load(this.page);
      } catch (err) {
        alert("删除失败");
      }
    }
  },
  mounted() {
    this.load(1);
  }
};
</script>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-row {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

input,
textarea {
  width: 100%;
  border: 1px solid #d5e1ef;
  background: #f9fbff;
  border-radius: 10px;
  padding: 10px;
  font-family: inherit;
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

button.light {
  background: #f2f7ff;
  color: #175a9b;
  border: 1px solid #c9dcf5;
}

button.danger {
  background: #ed4e4e;
}

.list-wrap {
  margin-top: 14px;
  display: grid;
  gap: 10px;
}

.item-card {
  border: 1px solid #e1ebf7;
  border-radius: 12px;
  padding: 12px;
}

.item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.badge {
  background: #eaf4ff;
  border-radius: 999px;
  padding: 4px 10px;
  color: #18558f;
  font-size: 0.84rem;
}

.actions {
  display: flex;
  gap: 8px;
}

.pager {
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
}

.hint {
  margin-top: 12px;
  color: #607792;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(20, 33, 47, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-body {
  width: min(620px, 100%);
  display: grid;
  gap: 10px;
}

.actions.right {
  justify-content: flex-end;
}

@media (max-width: 980px) {
  .filter-row {
    grid-template-columns: 1fr;
  }
}
</style>
