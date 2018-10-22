update employee set password = 'uZ5/tJEv03Bq2'
go
update branch_process_control set run_time_schedule = 'Minute1', is_active = 1 where process_name in ('Send New Switched Branch Txns to Central', 'Fetch New Switched Branch Txns From Central', 'Send Modified Switched Branch Txns to Central', 'Process Switched Branch Txn at Branch', 'Fetch Modified Switched Branch Txns From Central','SubAccountAndClubDocumentSync', 'QrCodeCleanup')
go
update branch_process_control set run_time_schedule = 'Minute15' , is_active = 1 where process_name in ('Monitor Branch Processes')
go
update branch_process_control set  run_time_schedule = 'Custom' , is_active = 0 where process_name in ('Branch StartOfDay Action Processor')
go
update branch_control set system_locked = 0, system_status = ''
go
update branch_process_action set continute_auth_code = 0, run_status = 'Unknown', run_comments = 'All stages run successfully' 
go
update branch_control set qr_code_enabled = 1
go

