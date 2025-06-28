+++
date = '{{ .Date }}'
draft = true
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
slug = '{{ substr (sha1 .File.Path) 0 8 }}'
+++
