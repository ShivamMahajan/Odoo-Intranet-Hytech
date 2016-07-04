 openerp.resource = function (openerp)
{   
    openerp.web.form.widgets.add('test', 'openerp.resource.Mywidget');
    openerp.resource.Mywidget = openerp.web.form.FieldChar.extend(
        {
        template : "test",
        init: function (view, code) {
            this._super(view, code);
            console.log('loading...');
        }
    });
}
