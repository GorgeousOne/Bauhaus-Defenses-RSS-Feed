Titel der Arbeit / *Title of the Thesis*:  
**{{ title }}**  

Datum und Uhrzeit / *Date and Time*:  
{{ date }}, {{ start }} - {{ end }}  

{% if location%}
Ort / *Location*:  
{{ location }}  
{% elif not note%}
Ort / *Location*:  
(keine Angabe / *no information*)  
{% endif %}

{% if note %}
Bemerkung / *Remarks*:  
{{ note }}  
{% endif %}

Zugeordnete Personen / *Responsible Instructors*:  
{% for examiner in examiners %}
- {{ examiner }}
{% endfor %}