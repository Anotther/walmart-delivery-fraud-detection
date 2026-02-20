# 🚀 Deploy no Streamlit Community Cloud

## Passo a Passo Rápido

### 1. Acesse o Streamlit Cloud
- URL: **https://share.streamlit.io/**
- Faça login com sua conta GitHub

### 2. Crie um Novo App
Clique em **"New app"** e configure:

```
Repository: seu-usuario/walmart-delivery-fraud-detection
Branch: main
Main file path: dashboard/app.py
```

### 3. Deploy!
Clique em **"Deploy!"** e aguarde ~2-3 minutos.

---

## ✅ Arquivos Preparados

- ✅ `packages.txt` - Dependências do sistema (libpq-dev)
- ✅ `requirements.txt` - Dependências Python
- ✅ `.streamlit/config.toml` - Tema Walmart
- ✅ `data/*.csv` - Dados commitados
- ✅ `dashboard/app.py` - Entry point

---

## 🔒 Segurança

**⚠️ IMPORTANTE**: Use repositório PRIVADO no GitHub (dados sensíveis)

---

## 📊 Configuração

- **Fonte de dados**: CSV (não requer PostgreSQL)
- **Caching**: 15 minutos
- **Tema**: Walmart blue (#004C91)

---

## 🔄 Atualizar o App

```bash
git push origin main
```

Redeploy automático em ~2 minutos.

---

## 🌐 URL do App

```
https://seu-app.streamlit.app
```

---

## 🆘 Troubleshooting

### App não inicia
- Verifique logs no Streamlit Cloud
- Teste localmente: `streamlit run dashboard/app.py`

### Erro "Module not found"
- Verifique `requirements.txt`

### Dados não carregam
- Confirme `data/*.csv` no repositório
- Verifique `DATA_SOURCE=csv`

---

## 🔗 Links

- [Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Deploy Tutorial](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
