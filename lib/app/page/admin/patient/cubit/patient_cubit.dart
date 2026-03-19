import 'package:bloc/bloc.dart';

import '../model/patient_model.dart';

part 'patient_state.dart';

class PatientCubit extends Cubit<PatientState> {
  PatientCubit()
      : super(PatientState(
          allPatients: _initialPatients,
          // Tab 0 = ALL → show every patient on init
          filteredPatients: _initialPatients,
          selectedTab: 0,
          searchQuery: '',
        ));

  static const List<PatientModel> _initialPatients = [
    PatientModel(
      name: 'Eleanor Vance',
      id: '#AURA-99283',
      phone: '+1 (555) 123-4567',
      image: 'https://i.pinimg.com/1200x/8d/51/16/8d5116e7e8f31b64a9ca530bef7a087e.jpg',
      isNew: false,
    ),
    PatientModel(
      name: 'Julian Blackwood',
      id: '#AURA-88124',
      phone: '+1 (555) 987-6543',
      image: 'https://i.pinimg.com/1200x/8d/51/16/8d5116e7e8f31b64a9ca530bef7a087e.jpg',
      isNew: false,
    ),
    PatientModel(
      name: 'Seraphina Thorne',
      id: '#AURA-11052',
      phone: '+1 (555) 246-8101',
      image: 'https://i.pinimg.com/1200x/8d/51/16/8d5116e7e8f31b64a9ca530bef7a087e.jpg',
      isNew: true,
    ),
    PatientModel(
      name: 'Alistair Sterling',
      id: '#AURA-44932',
      phone: '+1 (555) 369-1478',
      image: 'https://i.pinimg.com/1200x/8d/51/16/8d5116e7e8f31b64a9ca530bef7a087e.jpg',
      isNew: true,
    ),
  ];

  // ── Tab 0 = ALL, Tab 1 = NEW ──────────────────────────────
  void selectTab(int index) {
    emit(state.copyWith(
      selectedTab: index,
      filteredPatients: _applyFilter(
        isNewTab: index == 1,
        query: state.searchQuery,
      ),
    ));
  }

  void search(String query) {
    emit(state.copyWith(
      searchQuery: query,
      filteredPatients: _applyFilter(
        isNewTab: state.selectedTab == 1,
        query: query,
      ),
    ));
  }

  List<PatientModel> _applyFilter({
    required bool isNewTab,
    required String query,
  }) {
    return state.allPatients.where((patient) {
      // Tab filter: ALL shows everything, NEW filters by isNew flag
      final matchesTab = !isNewTab || patient.isNew;

      // Search: empty query shows all, otherwise match name / id / phone
      final matchesQuery = query.isEmpty ||
          patient.name.toLowerCase().contains(query.toLowerCase()) ||
          patient.id.toLowerCase().contains(query.toLowerCase()) ||
          patient.phone.toLowerCase().contains(query.toLowerCase());

      return matchesTab && matchesQuery;
    }).toList();
  }
}