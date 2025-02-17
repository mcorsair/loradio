# INSTALL

Для доступа к последовательному порту, 
необходимо добавить пользователя в группу `dialout`: 
```shell
sudo usermod -aG dialout $USER
```
и перегрузить Linux.
