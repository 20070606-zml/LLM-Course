# LLM-Course：第四周课程作业

本仓库保存第四周实际开发成果，项目目录为 `Agent/Practice01`。

本次提交范围为第四周 Practice01。使用 AI 分阶段完成开发，保留自然语言提示词、Git 版本及模拟接口验收材料。

进入 [Practice01 使用说明](Agent/Practice01/README.md) 查看配置、启动、测试及分阶段开发记录。
老师可先查看 [作业要求逐项对照](SUBMISSION.md)，再查看 [提示词](Agent/Practice01/PROMPTS.md)、[验收说明](Agent/Practice01/TEST_REPORT.md)和 [原始测试输出](Agent/Practice01/TEST_RESULTS.txt)。

## Git 状态

已经初始化本地 Git 仓库，分支为 `main`。课程要求的各阶段代码保存在 Git 提交历史中。
提交的作者标记为自动化工具 `Codex <codex@localhost>`，没有修改电脑全局 Git 身份配置。

目标公开仓库为 `20070606-zml/LLM-Course`。上传状态以 [提交说明](SUBMISSION.md) 的发布记录为准。
本地提交使用自动化工具身份，避免暴露个人邮箱；没有改写已有的分阶段开发历史。

`.gitignore` 中的 `config.ini` 规则会忽略所有子目录下的同名配置文件。仅提交不含密钥的 `config.example.ini`。

## 公开仓库与本地配置

公开仓库保存程序、使用说明、分阶段提示词、测试和占位配置模板。
`api_key` 是代码字段名，可以公开；真实密钥只能写入本机被忽略的 `config.ini`。
密码、GitHub 令牌、真实密钥、个人配置、私人邮箱和本机用户名不应写入公开文件、截图或提交说明。
`.env`、本地配置文件及常见私钥文件也已加入忽略规则。

配置缺失时可以使用模拟接口完成客户端测试，真实模型测试必须使用自己的本地配置；验收记录会区分这两种情况。
