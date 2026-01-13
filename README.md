<p align="center">
  <img src="assets/logo.jpg" width="200"/>
</p>

# fork from openmanus

# 修改点

- 架构：
  - 按manus的plan-do-review的流程来改造，而不是openmanus的react架构。
  - 使用agetnscope框架
- 功能点
  - 接入阿里web搜索服务，只保留这个。
  - 用户的输入请求，先做“清洗”，避免污染影响结果。
- 效率
  - web搜索结果全量提取，而不是摘要。
  - 效率优化提升，能并行的就并行。
  - 本地执行，还未做docker隔离等。


# 结果：亲测性能不错，结果初步比较满意。
