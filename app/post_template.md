Titel der Arbeit / *Title of the Thesis*:  
**{{ title }}**  

Datum und Uhrzeit / *Date and Time*:  
{{ date }}, {{ start }} - {{ end }}  

Ort / *Location*:  
{{ location }}  

{% if note %}
Bemerkung / *Remarks*:  
{{ note }}  
{% endif %}

Zugeordnete Personen / *Responsible Instructors*:  
{% for examiner in examiners %}
- {{ examiner }}
{% endfor %}