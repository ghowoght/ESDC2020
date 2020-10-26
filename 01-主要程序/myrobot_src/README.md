删除远程仓库：

```
git remote rm origin
```

添加远程仓库：

```
git remote add origin https://gitee.com/ghowoght/xx.git
```

本地上传：

```
git push -u origin master
```

更新本地：

```
git pull origin master
```



### 免密码上传

需要建立远端和本地的SSH连接：

```
git remote rm origin
git remote add origin git@gitee.com:ghowoght/myrobot_src.git
```

重新在本地生成SSH

```
ssh-keygen -t rsa -C "2550319354@qq.com"
```

查看`id_rsa.pub`，并复制

```
cat ~/.ssh/id_rsa.pub 
```

然后在gitee->管理->部署公钥管理中添加个人公钥，注意是**个人公钥**