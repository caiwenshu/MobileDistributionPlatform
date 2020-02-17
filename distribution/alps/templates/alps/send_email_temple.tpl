{% extends "mail_templated/base.tpl" %}


{% block subject %}
【{{ appInfo.name }}】【{{ platform }}】【{{appInfo.jira_version}}】【{{appInfo.buildType}}】【Build:{{appInfo.id}}】 {% block subject_content %}{{ appInfo.name }}_{{ platform }} {% endblock %}
{% endblock %}


{% block html %}

<br />
<div>
    <h2>{{ appInfo.name }}【Build:{{appInfo.id}}】</h2>
</div>

<div>
    <strong>操作系统:</strong>
    <br />
    {{ platform }}
</div>
<br />
<div>
    <strong>版本:</strong>
    <br />
    {{ appInfo.serverVersion }}
</div>
<br />
<div>
    <strong>构建类型:</strong>
    <br />
    {{ appInfo.buildType }}
</div>
<br />
  <div>
      <strong>上传时间:</strong>
      <br />
      {{ appInfo.createTime|date:"Y-m-d H:i" }}
  </div>
<br />

    <style type="text/css">
			tr.first td{
				background: #f0f0f0;
				color: #4a4a4a;
			}
			td{
				background: #f6f6f6;
			}
		</style>



<div>
      <strong>Ready For QA:</strong>
      <br />
      <table style="margin-left:20px;" border="0" cellspacing="0" cellpadding="12">

             <tr class="first">
				<td>状态</td>
				<td>类型</td>
				<td>编号</td>
				<td>标题</td>
				<td>Assignee</td>
				<td>更新时间</td>
			</tr>

      {% for story in story_list %}

            <tr class="second">
				<td>{{story.status}}</td>
				<td>{{story.issuetype}}</td>
				<td>{{story.key}}</td>
				<td>{{story.summary}}</td>
				<td>{{story.assignee}}</td>
				<td>{{story.updated}}</td>
			</tr>

      {% endfor %}

		</table>
  </div>

{% if  platform == "Android" %}
   <br />
   <div>
      <strong>Android Lint 分析:</strong>
      <br />
      <table style="margin-left:20px;" border="0" cellspacing="0" cellpadding="12">

             <tr class="first">
				<td>Fatal</td>
				<td>Error</td>
				<td>Warning</td>
				<td>Ignore</td>
				<td>Information</td>
				<td>link Detail</td>
			</tr>
            <tr class="second">
				<td>{{android_summary_lint.module_lint_severity_fatal}}</td>
				<td>{{android_summary_lint.module_lint_severity_error}}</td>
				<td>{{android_summary_lint.module_lint_severity_warning}}</td>
				<td>{{android_summary_lint.module_lint_severity_ignore}}</td>
				<td>{{android_summary_lint.module_lint_severity_information}}</td>

				<td>{{android_summary_lint.get_preview_android_lint_detail}}</td>
			</tr>

		</table>
  </div>

{% endif %}



<br />
  <div>
      <strong>唯一标识:</strong>
      <br />
      {{ appInfo.bundle_identifier }}
  </div>
<br />
  <div>
      <strong>访问地址:</strong>
      <br />
      {{ appInfo.get_qrcode_url }}
  </div>
<br />
  <div>
      <strong>如果在电脑上直接用手机扫描二维码安装:</strong>
      <br />
      <img src ="{{appQRCodeURL}}"/><p>
  </div>

 <br />
    <div>
        <strong>GIT 地址:</strong>
        <br />
      {{ appInfo.gitUrl }}
    </div>

    <br />
      <div>
          <strong>GIT 分支:</strong>
          <br />
        {{ appInfo.gitBranch }}
      </div>

        <br />
          <div>
              <strong>改动记录:</strong>
              <br />
              <br />
              <div style="margin-left:20px;color:#9b9b9b">
              {{ appInfo.changeLog  | linebreaksbr }}
              </div>
          </div>

         <br />
         <br />
         <br />
         <br />
{% endblock %}
