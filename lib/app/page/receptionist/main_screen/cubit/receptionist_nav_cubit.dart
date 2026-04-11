import 'package:bloc/bloc.dart';

part 'receptionist_nav_state.dart';

class ReceptionistNavCubit extends Cubit<ReceptionistNavState> {
  ReceptionistNavCubit() : super(const ReceptionistNavState());

  void selectTab(ReceptionistTab tab) =>
      emit(ReceptionistNavState(activeTab: tab));
}
