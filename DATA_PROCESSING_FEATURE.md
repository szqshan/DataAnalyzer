# 数据处理和清洗功能说明

## 功能概述

DataAnalyzer v1.2 新增了强大的数据处理和清洗模块，支持多种文件格式和智能数据质量评估。用户上传数据文件时，系统会自动进行数据质量检查、清洗和优化，确保数据分析的准确性和效率。

## 🚀 核心功能

### 1. 多格式文件支持
- **CSV文件** (.csv) - 支持多种编码格式自动检测
- **Excel文件** (.xlsx, .xls) - 支持多工作表
- **JSON文件** (.json) - 支持嵌套结构自动展平
- **TSV文件** (.tsv) - 制表符分隔值文件
- **TXT文件** (.txt) - 自动检测分隔符

### 2. 智能数据质量评估
- **基础信息统计**: 行数、列数、内存使用、文件大小
- **列级别分析**: 数据类型、缺失值、唯一值统计
- **数据质量问题检测**:
  - 缺失值分析
  - 重复行检测
  - 数据类型不匹配
  - 异常值检测（IQR方法）
  - 格式一致性检查
- **质量评分**: 0-100分的综合质量评分

### 3. 自动数据清洗
- **重复数据处理**: 自动删除完全重复的行
- **缺失值处理**:
  - 智能填充：数值列用中位数，文本列用众数
  - 阈值删除：缺失值超过设定阈值的列自动删除
- **数据类型优化**:
  - 自动识别并转换数值类型
  - 日期时间格式自动识别
- **文本标准化**:
  - 去除首尾空格
  - 统一大小写格式
- **列名清理**: 标准化列名格式

### 4. 处理报告生成
- **质量评估报告**: 详细的数据质量分析
- **清洗操作日志**: 记录所有清洗操作
- **建议实施情况**: 跟踪已实施和待实施的建议
- **数据变化统计**: 清洗前后的数据对比

## 📊 API接口

### 1. 文件预览接口
```
POST /api/preview-file
```
**功能**: 预览文件内容和数据质量评估（不导入数据库）

**请求参数**:
- `file`: 上传的文件

**返回数据**:
```json
{
  "success": true,
  "message": "文件预览成功",
  "data": {
    "filename": "data.xlsx",
    "file_format": ".xlsx",
    "quality_report": {
      "basic_info": {...},
      "column_analysis": {...},
      "data_quality_issues": {...},
      "recommendations": [...],
      "overall_score": 85
    },
    "preview_data": {
      "shape": [1000, 10],
      "columns": [...],
      "head": [...],
      "basic_stats": {...}
    }
  }
}
```

### 2. 文件上传接口（增强版）
```
POST /api/upload
```
**功能**: 上传文件并自动处理清洗后导入数据库

**新增返回字段**:
- `file_format`: 文件格式
- `quality_report`: 数据质量报告
- `cleaning_log`: 清洗操作日志
- `processing_report`: 处理总结报告

## 🛠 配置选项

### 数据清洗配置
```python
processing_options = {
    "enable_cleaning": True,  # 是否启用数据清洗
    "cleaning_options": {
        "remove_duplicates": True,      # 删除重复行
        "handle_missing": "auto",       # 缺失值处理: auto/drop/fill
        "fix_data_types": True,         # 修复数据类型
        "standardize_text": True,       # 标准化文本
        "missing_threshold": 80         # 缺失值删除阈值（百分比）
    }
}
```

### 缺失值处理策略
- **auto**: 智能处理（数值列用中位数，文本列用众数）
- **drop**: 删除包含缺失值的行
- **fill**: 使用指定值填充

## 📈 质量评分算法

质量评分基于以下因素计算（满分100分）：

1. **缺失值扣分**: 缺失值百分比 × 0.5（最多扣30分）
2. **重复行扣分**: 重复行百分比 × 0.3（最多扣15分）
3. **数据类型问题**: 每个问题扣5分（最多扣20分）
4. **异常值扣分**: 每列异常值扣3分（最多扣15分）
5. **格式问题扣分**: 每个格式问题扣5分（最多扣20分）

## 🔍 异常值检测

使用IQR（四分位距）方法检测异常值：
- Q1: 第一四分位数（25%分位数）
- Q3: 第三四分位数（75%分位数）
- IQR = Q3 - Q1
- 下界 = Q1 - 1.5 × IQR
- 上界 = Q3 + 1.5 × IQR
- 超出[下界, 上界]范围的值被标记为异常值

## 📝 使用示例

### 1. 预览文件质量
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/preview-file', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('质量评分:', data.data.quality_report.overall_score);
    console.log('建议:', data.data.quality_report.recommendations);
});
```

### 2. 上传并处理文件
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('清洗操作:', data.data.cleaning_log.operations);
    console.log('处理报告:', data.data.processing_report);
});
```

## 🎯 处理流程

1. **文件上传**: 用户选择并上传文件
2. **格式检测**: 自动识别文件格式
3. **文件读取**: 使用适当的方法读取文件内容
4. **质量评估**: 分析数据质量并生成报告
5. **数据清洗**: 根据配置自动清洗数据
6. **数据导入**: 将处理后的数据导入SQLite数据库
7. **报告生成**: 生成完整的处理报告

## 🚨 注意事项

1. **文件大小限制**: 建议单个文件不超过100MB
2. **内存使用**: 大文件处理时会占用较多内存
3. **编码支持**: CSV文件支持UTF-8、GBK、GB2312等编码
4. **Excel限制**: 默认读取第一个工作表
5. **数据备份**: 原始数据在清洗前会保留副本

## 🔧 故障排除

### 常见问题
1. **文件读取失败**: 检查文件格式和编码
2. **内存不足**: 减小文件大小或增加系统内存
3. **清洗失败**: 检查数据格式和配置参数
4. **导入失败**: 确认数据库权限和磁盘空间

### 错误代码
- `UNSUPPORTED_FORMAT`: 不支持的文件格式
- `READ_ERROR`: 文件读取错误
- `ENCODING_ERROR`: 编码识别失败
- `PROCESSING_ERROR`: 数据处理错误
- `DATABASE_ERROR`: 数据库操作错误

## 📊 性能指标

- **文件读取速度**: 约1MB/秒
- **质量评估时间**: 1万行数据约1-2秒
- **清洗处理时间**: 1万行数据约2-5秒
- **内存使用**: 约为文件大小的3-5倍

## 🔄 版本更新

### v1.2.0 新功能
- ✅ 多格式文件支持
- ✅ 智能数据质量评估
- ✅ 自动数据清洗
- ✅ 处理报告生成
- ✅ 文件预览功能

### 后续规划
- 🔄 支持更多文件格式（Parquet、Avro等）
- 🔄 机器学习异常检测
- 🔄 自定义清洗规则
- �� 批量文件处理
- 🔄 数据血缘追踪 