import 'package:aura/app/page/admin/patient/view/patient_list_screen.dart';
import 'package:aura/app/page/admin/payemt/view/payment_list_screen.dart';
import 'package:aura/app/page/receptionist/Appointments/view/Appointment_list_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../dashboard/view/receptionist_dashboard.dart';
import '../cubit/receptionist_nav_cubit.dart';
import '../view/receptionist_bottom_nav_bar.dart';

class ReceptionistMainScreen extends StatelessWidget {
  const ReceptionistMainScreen({super.key});

  static const _pages = <Widget>[
    ReceptionistDashboard(),
    AppointmentListScreen(),
    PatientsScreen(),
    PaymentListScreen(),
    ReceptionistSettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ReceptionistNavCubit(),
      child: BlocBuilder<ReceptionistNavCubit, ReceptionistNavState>(
        builder: (context, state) {
          return Scaffold(
            backgroundColor: const Color(0xFF0A0A0A),
            body: IndexedStack(
              index: state.activeTab.index,
              children: _pages,
            ),
            bottomNavigationBar: const ReceptionistBottomNavBar(),
          );
        },
      ),
    );
  }
}


// receptionist_patients_screen.dart
class ReceptionistPatientsScreen extends StatelessWidget {
  const ReceptionistPatientsScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: Text('UPCOMING SCREEN')));
}

// receptionist_settings_screen.dart
class ReceptionistSettingsScreen extends StatelessWidget {
  const ReceptionistSettingsScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: Text('UPCOMING SCREEN')));
}
