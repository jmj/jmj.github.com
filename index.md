---
layout: page
title: Brain Dump
tagline: Supporting tagline
---
{% include JB/setup %}

##Welcome
Here you may find strange artifacts from my brain.  Thoughts on life, family, technology, and politics.

We don't do comments here (managing comments takes to much time), but I do love to discuss.  If you want to discuss more, hit me up on facebook or shoot me an email.  

<div class="posts">
{% for post in site.posts limit:10 %}
    <h3><a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a> - {{ post.date | date_to_string }}</h3>
    {{ post.excerpt }}
{% endfor %}
</div>

