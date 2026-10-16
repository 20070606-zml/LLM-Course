# LLM 课程练习

本仓库保存第四周实际开发成果，项目目录为 `Agent/Practice01`。

目前没有导入前三次课程代码；当前工作目录原先为空，不能用空壳目录代替原来的作业。

进入 [Practice01 使用说明](Agent/Practice01/README.md) 查看配置、启动、测试及分阶段开发记录。

## Git 状态

已经初始化本地 Git 仓库，分支为 `main`。课程要求的各阶段代码保存在 Git 提交历史中。
提交的作者标记为自动化工具 `Codex <codex@localhost>`，没有修改电脑全局 Git 身份配置。

尚未绑定 GitHub 远程仓库，也没有上传。当前环境没有已配置的 Git 作者身份或 GitHub 仓库地址。
创建自己的 GitHub 仓库后，可以在本目录执行（替换其中的占位内容）：

```powershell
git config user.name "你的名字"
git config user.email "你的 GitHub 提交邮箱"
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

`.gitignore` 中的 `config.ini` 规则会忽略所有子目录下的同名配置文件。仅提交不含密钥的 `config.example.ini`。
