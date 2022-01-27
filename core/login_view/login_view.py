from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages

from core.models.Employee import Employee
from core.models.Dispute import Roster

class LoginView(View):
    template_name = 'core/login.html'

    def get(self, req):
        clients = Roster.objects.values_list('client',flat=True).distinct()
        ctx = {
            'clients':clients
        }
        return render(req, self.template_name,ctx)

    def post(self, req):
        loginid = req.POST.get('username', None)
        password = req.POST.get('password', None)
        client = req.POST.get('client',None)
        role = req.POST.get('role', None)

        if (loginid != None) and (password != None) and (role != None) and (client != None):
            try:
                is_present = Roster.objects.filter(zipwire=loginid.strip().lower(),client=client)
                print(is_present)
                if is_present.exists():
                    roster_obj = is_present.first()
                    try:
                        user = Employee.objects.filter(loginId = loginid, deluxCode = roster_obj.deluxcode)
                        if user.exists():
                            user = user.first()
                            print(user)
                            if user:
                                valid_pass = check_password(password,user.password)
                                print(valid_pass)
                                if valid_pass:
                                    if role == 'AGT':
                                        login(req, user)
                                        # return redirect('core:home')
                                        return redirect('core:agent-payroll')
                                    if role == 'OPER_MAN' and user.role=='OPER_MAN':
                                        login(req, user)
                                        return redirect('core:operations')
                                    if role == 'TEAM_SUP' and user.role=='TEAM_SUP':
                                        login(req, user)
                                        return redirect('core:super-home')
                                    if role == 'FIN' and user.role=='FIN':
                                        login(req,user)
                                        return redirect('core:finance-index')
                        messages.error(req, 'Username or Password not matched!')
                        return redirect('core:login')
                    except Employee.DoesNotExist:
                        messages.error(req, 'Username or Password not matched!')
                        return redirect('core:login')
            except Roster.DoesNotExist:
                messages.error(req, 'Username or Password not matched!')
                return redirect('core:login')
            messages.error(req, 'Username or Password or Project not matched!')
            return redirect('core:login')


def LogoutView(req):
    logout(req)
    return redirect('core:login')


class ChangePasswordView(LoginRequiredMixin,View):
    template_name = 'recover.html'
    title = 'Change password'

    def get(self,req):
        ctx = {
            'title':self.title,
        }
        return render(req,self.template_name,ctx)

    def post(self,req):
        currentPassword = req.POST['currentPassword']
        new_password = req.POST['new_password1']
        confirm_password = req.POST['new_password2']

        if new_password != confirm_password:
            messages.warning(req,'confirm password not matched!')
            return redirect('core:change-password')

        if req.user.check_password(currentPassword):
            user = Employee.objects.get(pk=req.user.pk)
            user.password = make_password(new_password)
            user.save()
            messages.success(req, 'Password change suscess, Please login again!')
            return redirect('core:logout')
        else:
            messages.error(req, 'Please enter correct password')
            return redirect('core:change-password')