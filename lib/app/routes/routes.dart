import 'package:aura/app/page/admin/admin_main_screen/view/admin_main_screen.dart';
import 'package:aura/app/page/admin/cinic_operations/view/clinic_operation_screen.dart';
import 'package:aura/app/page/admin/inventory/view/inventory_detail_screen.dart';
import 'package:aura/app/page/admin/inventory/view/inventory_manage_screen.dart';
import 'package:aura/app/page/admin/patient/view/add_patient_screen.dart';
import 'package:aura/app/page/admin/patient/view/patient_detail_screen.dart';
import 'package:aura/app/page/admin/rooms/view/room_list_screen.dart';
import 'package:aura/app/page/admin/rooms/view/room_manage_screen.dart';
import 'package:aura/app/page/admin/service/view/service_detail_screen.dart';
import 'package:aura/app/page/admin/service/view/service_list_screen.dart';
import 'package:aura/app/page/admin/service/view/service_manage_screen.dart';
import 'package:aura/app/page/admin/staff/view/staff_detail_screen.dart';
import 'package:aura/app/page/admin/staff/view/add_edit_staff_screen.dart';
import 'package:aura/app/page/receptionist/Appointments/view/booking_screen.dart';
import 'package:aura/app/page/receptionist/main_screen/view/receptionist_main_screen.dart';
import 'package:aura/app/page/select_role/view/select_role_screen.dart';
import 'package:aura/app/page/therapist/dashboard/view/therapist_dashboard.dart';
import 'package:aura/app/page/therapist/main_screen/view/therapist_main_screen.dart';
import 'package:aura/app/page/therapist/appointment/view/therapist_appointment_detail_screen.dart';


import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:get/get_navigation/src/routes/transitions_type.dart'
    as transitions_type;
import 'package:aura/app/page/admin/payemt/view/payment_list_screen.dart';
import '../page/admin/user_managment/view/user_management_screen.dart';
import '../page/authentication/sign_in/sign_in_screen.dart';
import '../page/receptionist/Appointments/view/appointment_detail_screen.dart';
import '../page/splash/splash_screen.dart';
import 'names.dart';
import 'package:aura/app/page/admin/payemt/view/paymnet_detail_screen.dart';
import 'package:aura/app/page/admin/payemt/view/add_edit_payment_screen.dart';
import '../page/admin/patient/model/patient_model.dart';

const navigationTransition = transitions_type.Transition.native;
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

class Routes {
  static final routes = [
    GetPage(
      name: PageRoutes.splashScreen,
      page: () => const SplashScreen(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.selectRoleScreen,
      page: () => const SelectRoleScreen(),
      transition: navigationTransition,
    ),
    // GetPage(
    //   name: PageRoutes.signupScreen,
    //   page: () => const SignupScreen(),
    //   transition: navigationTransition,
    // ),
    GetPage(
      name: PageRoutes.signInScreen,
      page: () => const LoginScreen(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.adminMainScreen,
      page: () => const AdminMainScreen(),
      transition: navigationTransition,
    ),
 
    GetPage(
      name: PageRoutes.staffDetailScreen,
      page: () => const StaffDetailScreen(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.addEditStaffScreen,
      page: () => AddEditStaffScreen(isEdit: Get.arguments ?? false),
      transition: navigationTransition,
    ),


    GetPage(
      name: PageRoutes.patientDetailScreen,
      page: () => const PatientDetailScreen(),
      transition: navigationTransition,
    ),


    GetPage(
      name: PageRoutes.serviceListScreen,
      page: () => const ServiceListScreen(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.serviceManageScreen,
      page: () => const ServiceManageScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.serviceDetailScreen,
      page: () => const ServiceDetailScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.roomManageScreen,
      page: () => const RoomManageScreen(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.roomListScreen,
      page: () => const RoomListScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.addPatientScreen,
      page: () {
        final args = Get.arguments;
        final isEdit = args != null;
        return AddPatientScreen(
          isedit: isEdit,
          patient: args is PatientModel ? args : null,
        );
      },
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.clinicOperation,
      page: () => const ClinicOperationsScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.inventoryManageScreen,
      page: () => InventoryManageScreen(isEdit: Get.arguments ?? false),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.inventoryDetailScreen,
      page: () => const InventoryDetailScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.paymentListScreen,
      page: () => const PaymentListScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.paymentDetailScreen,
      page: () => const InvoiceDetailScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.addEditPaymentScreen,
      page: () => const AddEditPaymentScreen(),
      transition: navigationTransition,
    ),

  GetPage(
      name: PageRoutes.userManagementScreen,
      page: () => const ManageUsersScreen(),
      transition: navigationTransition,
    ),







    //-----RECPTIONIST---------//
    GetPage(
      name: PageRoutes.receptioninstMainScreen,
      page: () => const ReceptionistMainScreen(),
      transition: navigationTransition,
    ),

    GetPage(
      name: PageRoutes.appointmentDetailScreen,
      page: () => const AppointmentDetailScreen(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.bookingScreen,
      page: () => const BookingScreen(),
      transition: navigationTransition,
    ),

    //-----THERAPIST---------//
    GetPage(
      name: PageRoutes.therapistMainScreen,
      page: () => const TherapistMainScreen(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.therapistDashboard,
      page: () => const TherapistDashboard(),
      transition: navigationTransition,
    ),
    GetPage(
      name: PageRoutes.therapistAppointmentDetailScreen,
      page: () => const TherapistAppointmentDetailScreen(),
      transition: navigationTransition,
    ),
  ];
}
