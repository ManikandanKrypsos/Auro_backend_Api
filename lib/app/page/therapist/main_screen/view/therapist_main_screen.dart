
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../admin/patient/view/patient_list_screen.dart';
import '../../appointment/view/therapist_appointment_list_screen.dart';
import '../../dashboard/view/therapist_dashboard.dart';
import '../../product_usage/view/product_usage_screen.dart';
import '../../settings/view/therapist_setting_screen.dart';
import '../cubit/therapist_nav_cubit.dart';
import '../view/receptionist_bottom_nav_bar.dart';

class TherapistMainScreen extends StatelessWidget {
  const TherapistMainScreen({super.key});

  static const _pages = <Widget>[
    TherapistDashboard(),
    TherapistAppointmentListScreen(),
    PatientsScreen(isReadOnly: true),
    ProductUsageScreen(),
    TherapistSettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => TherapistNavCubit(),
      child: BlocBuilder<TherapistNavCubit, TherapistNavState>(
        builder: (context, state) {
          return Scaffold(
            backgroundColor: const Color(0xFF0A0A0A),
            body: IndexedStack(
              index: state.activeTab.index,
              children: _pages,
            ),
            bottomNavigationBar: const TherapistBottomNavBar(),
          );
        },
      ),
    );
  }
}




