from flask import Blueprint
from flask_restful import Api

from autoshop.api.resources import (
    AccountEntriesList,
    AccountEntriesResource,
    AccountList,
    AccountResource,
    AccountTypeList,
    AccountTypeResource,
    VehicleList,
    VehicleResource,
    CustomerList,
    CustomerResource,
    EntityList,
    EntityResource,
    EntityVendorList,
    EntityVendorResource,
    EntryList,
    EntryResource,
    PaymentTypeList,
    PaymentTypeResource,
    CustomerTypeList,
    CustomerTypeResource,
    QueryList,
    RoleList,
    RoleResource,
    SearchList,
    SettingList,
    SettingResource,
    VehicleModelList,
    VehicleModelResource,
    TransactionList,
    TransactionResource,
    TransactionTypeList,
    TransactionTypeResource,
    UserList,
    UserResource,
    VendorList,
    VendorResource,
    VehicleTypeResource,
    VehicleTypeList,
    AccessLogResource, AccessLogList
)

blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(blueprint)


api.add_resource(UserResource, "/users/<int:user_id>")
api.add_resource(UserList, "/users")
api.add_resource(RoleResource, "/roles/<int:role_id>")
api.add_resource(RoleList, "/roles")

api.add_resource(EntityResource, "/entities/<int:entity_id>")
api.add_resource(EntityList, "/entities")
api.add_resource(
    EntityVendorResource, "/entities/<int:entity_id>/vendors/<int:vendor_id>"
)
api.add_resource(EntityVendorList, "/entities/vendors")
api.add_resource(VendorResource, "/vendors/<int:vendor_id>")
api.add_resource(VendorList, "/vendors")
api.add_resource(CustomerResource, "/customers/<int:customer_id>")
api.add_resource(CustomerList, "/customers")
api.add_resource(VehicleResource, "/vehicles/<int:vehicle_id>")
api.add_resource(VehicleList, "/vehicles")
api.add_resource(VehicleTypeResource, "/vehicle_types/<int:vehicle_type_id>")
api.add_resource(VehicleTypeList, "/vehicle_types")
api.add_resource(VehicleModelResource, "/vehicle_models/<int:vehicle_model_id>")
api.add_resource(VehicleModelList, "/vehicle_models")

api.add_resource(AccountTypeResource, "/account_types/<int:account_type_id>")
api.add_resource(AccountTypeList, "/account_types")
api.add_resource(AccountResource, "/accounts/<int:account_id>")
api.add_resource(AccountList, "/accounts")
api.add_resource(AccountEntriesResource, "/accounts/entries/<int:account_id>")
api.add_resource(AccountEntriesList, "/accounts/entries")
api.add_resource(CustomerTypeResource, "/customer_types/<int:customer_type_id>")
api.add_resource(CustomerTypeList, "/customer_types")
api.add_resource(EntryResource, "/entries/<int:entry_id>")
api.add_resource(EntryList, "/entries")
api.add_resource(TransactionResource, "/transactions/<int:transaction_id>")
api.add_resource(TransactionList, "/transactions")

api.add_resource(
    TransactionTypeResource, "/transaction_types/<int:transaction_type_id>"
)
api.add_resource(TransactionTypeList, "/transaction_types")
api.add_resource(PaymentTypeResource, "/payment_types/<int:payment_type_id>")
api.add_resource(PaymentTypeList, "/payment_types")
api.add_resource(SettingResource, "/settings/<int:setting_id>")
api.add_resource(SettingList, "/settings")


api.add_resource(SearchList, "/search")
api.add_resource(QueryList, "/query")

api.add_resource(AccessLogResource, '/access_logs/<int:access_log_id>')
api.add_resource(AccessLogList, '/access_logs')