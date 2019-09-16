from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Expense, Entry


class ExpenseSchema(ma.ModelSchema):
    class Meta:
        model = Expense
        sqla_session = db.session

        additional = ("creator",)


class ExpenseResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, expense_id):
        schema = ExpenseSchema()
        expense = Expense.query.get_or_404(expense_id)
        return {"expense": schema.dump(expense).data}

    def put(self, expense_id):
        schema = ExpenseSchema(partial=True)
        expense = Expense.query.get_or_404(expense_id)
        expense, errors = schema.load(request.json, instance=expense)
        if errors:
            return errors, 422
        expense.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "expense updated", "expense": schema.dump(expense).data}

    def delete(self, expense_id):
        expense = Expense.query.get_or_404(expense_id)
        db.session.delete(expense)
        db.session.commit()

        return {"msg": "expense deleted"}


class ExpenseList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ExpenseSchema(many=True)
        if request.args.get("item") or request.args.get('from'):
            from_date = request.args.get('from')
            to_date = request.args.get('to')
            item = request.args.get('item')

            query = Expense.query
            if item != '':
                query = query.filter_by(item=item)
            if from_date and to_date:
                query = query.filter(Expense.date_created.between(from_date,to_date))
        else:
            query = Expense.query

        return paginate(query.order_by(Expense.date_created.desc()), schema)

    def post(self):
        schema = ExpenseSchema()
        expense, errors = schema.load(request.json)
        if errors:
            return errors, 422

        expense.created_by = get_jwt_identity()

        if Expense.get(reference=expense.reference):
            return {"msg": "The supplied reference already exists"}, 409
        
        try:
            entry = Entry.init_expense(expense)
            expense.save()
            entry.transact()
            
            return {"msg": "expense created", "expense": schema.dump(expense).data}, 201
        except Exception as e:
            expense.status = 'FAILED'
            expense.reason = str(e.args[0])
            expense.update()
            print(e)
            return {"msg": e.args[0]}, e.args[1] if len(e.args) > 1 else 500
