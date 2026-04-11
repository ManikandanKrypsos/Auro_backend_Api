part of 'therapist_nav_cubit.dart';

enum TherapistTab { dashboard, schedule, patients,paymnets, settings, }

class TherapistNavState {
  final TherapistTab activeTab;
  const TherapistNavState({this.activeTab = TherapistTab.dashboard});
}
