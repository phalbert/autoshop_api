from flask import Blueprint
from flask_restful import Api

from autoshop.api.resources import (
    AccountEntriesList,AccountEntriesResource,
    AccountList,AccountResource,
    AccountTypeList,AccountTypeResource,
    VehicleList,VehicleResource,
    CustomerList,CustomerResource,
    EntityList,EntityResource,
    EntityVendorList,EntityVendorResource,
    EntryList,EntryResource,
    PaymentTypeList,PaymentTypeResource,
    CustomerTypeList,CustomerTypeResource,
    QueryList,RoleList,RoleResource,
    SearchList,SettingList,SettingResource,
    VehicleModelList,VehicleModelResource,
    TransactionList,TransactionResource,
    TransactionTypeList,TransactionTypeResource,
    UserList,UserResource,
    VendorList,VendorResource,
    VehicleTypeResource,VehicleTypeList,
    AccessLogResource, AccessLogList,
    ServiceResource, ServiceList,
    ServiceRequestResource, ServiceRequestList,
    WorkItemResource, WorkItemList,
    PartResource,PartList,
    PartCategoryResource,PartCategoryList,
    EmployeeTypeResource, EmployeeTypeList,
    EmployeeResource, EmployeeList,
    JobResource, JobList, JobItemResource, JobItemList,
    MakeResource, MakeList, PartLogResource, PartLogList,
    LocalPurchaseOrderList, LocalPurchaseOrderResource,
    LpoItemList, LpoItemResource
)

blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(blueprint)

api.add_resource(LpoItemResource, "/lpo_items/<int:lpo_item_id>")
api.add_resource(LpoItemList, "/lpo_items")
api.add_resource(LocalPurchaseOrderResource, "/lpos/<int:lpo_id>")
api.add_resource(LocalPurchaseOrderList, "/lpos")
api.add_resource(PartLogResource, "/part_logs/<int:part_log_id>")
api.add_resource(PartLogList, "/part_logs")
api.add_resource(MakeResource, "/brands/<int:make_id>")
api.add_resource(MakeList, "/brands")
api.add_resource(JobItemResource, "/job_items/<int:job_item_id>")
api.add_resource(JobItemList, "/job_items")
api.add_resource(JobResource, "/jobs/<int:job_id>")
api.add_resource(JobList, "/jobs")
api.add_resource(EmployeeResource, "/employees/<int:employee_id>")
api.add_resource(EmployeeList, "/employees")
api.add_resource(EmployeeTypeResource, "/employee_types/<int:employee_type_id>")
api.add_resource(EmployeeTypeList, "/employee_types")
api.add_resource(PartCategoryResource, "/part_categories/<int:part_category_id>")
api.add_resource(PartCategoryList, "/part_categories")
api.add_resource(PartResource, "/parts/<int:part_id>")
api.add_resource(PartList, "/parts")
api.add_resource(ServiceResource, "/services/<int:service_id>")
api.add_resource(ServiceList, "/services")
api.add_resource(ServiceRequestResource, "/service_requests/<int:service_request_id>")
api.add_resource(ServiceRequestList, "/service_requests")
api.add_resource(WorkItemResource, "/work_items/<int:work_item_id>")
api.add_resource(WorkItemList, "/work_items")

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